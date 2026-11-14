#!/usr/bin/env python3
"""DocSolver - 파일을 추가하면 내용을 검색하고, 문제를 찾아 솔루션을 제시하는 앱.

실행:  python3 server.py [포트]     (기본 8000, http://localhost:8000)
외부 패키지 불필요 (표준 라이브러리만 사용).
선택: PDF 는 `pip install pypdf` 시 지원, AI 답변은 ANTHROPIC_API_KEY 설정 시 활성화.
"""
import json, math, os, re, sys, threading, zipfile, io, urllib.request, urllib.parse
from collections import Counter, defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from kb import RULES, SEV_ORDER

BASE = Path(__file__).parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)
MAX_BYTES = 20 * 1024 * 1024
CHUNK_LINES, OVERLAP, CHUNK_CHARS = 14, 3, 1400

# ---------------------------------------------------------------- 텍스트 추출
def extract_text(name: str, raw: bytes) -> str:
    ext = Path(name).suffix.lower()
    if ext == ".docx":
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            xml = z.read("word/document.xml").decode("utf-8", "ignore")
        xml = re.sub(r"</w:p>", "\n", xml)
        xml = re.sub(r"<[^>]+>", "", xml)
        return re.sub(r"&lt;", "<", re.sub(r"&gt;", ">", re.sub(r"&amp;", "&", xml)))
    if ext == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ValueError("PDF 는 `pip install pypdf` 후 사용할 수 있습니다.")
        return "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(raw)).pages)
    if b"\x00" in raw[:4096]:
        raise ValueError("지원하지 않는 바이너리 파일입니다.")
    for enc in ("utf-8-sig", "cp949", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")

# ---------------------------------------------------------------- 토크나이저 / BM25
_tok_en = re.compile(r"[a-z0-9_]+")
_tok_ko = re.compile(r"[가-힣]+")

def tokenize(text: str):
    text = text.lower()
    toks = _tok_en.findall(text)
    for w in _tok_ko.findall(text):
        if len(w) == 1:
            toks.append(w)
        else:  # 한글은 bi-gram 으로 조사/어미 변형에 강하게
            toks.extend(w[i:i + 2] for i in range(len(w) - 1))
    return toks

class Index:
    def __init__(self):
        self.lock = threading.RLock()
        self.files = {}      # name -> {"text","lines","size"}
        self.chunks = []     # {"file","start","end","text","tf","len"}
        self.df = Counter()
        self.avg = 0.0

    def rebuild(self):
        with self.lock:
            self.chunks, self.df = [], Counter()
            for name, f in self.files.items():
                lines = f["lines"]
                i = 0
                while i < len(lines):
                    j, size = i, 0
                    while j < len(lines) and (j - i < CHUNK_LINES) and size < CHUNK_CHARS:
                        size += len(lines[j]) + 1
                        j += 1
                    j = max(j, i + 1)
                    text = "\n".join(lines[i:j])
                    toks = tokenize(text)
                    self.chunks.append({"file": name, "start": i + 1, "end": j, "text": text,
                                        "tf": Counter(toks), "len": len(toks) or 1})
                    if j >= len(lines):
                        break
                    i = max(j - OVERLAP, i + 1)
            for c in self.chunks:
                self.df.update(c["tf"].keys())
            self.avg = (sum(c["len"] for c in self.chunks) / len(self.chunks)) if self.chunks else 1.0

    def add(self, name, text, size):
        with self.lock:
            self.files[name] = {"text": text, "lines": text.splitlines(), "size": size}
            self.rebuild()

    def remove(self, name):
        with self.lock:
            self.files.pop(name, None)
            self.rebuild()

    def search(self, query, k=8):
        q = tokenize(query)
        if not q:
            return []
        n, k1, b = len(self.chunks), 1.5, 0.75
        out = []
        with self.lock:
            for c in self.chunks:
                s = 0.0
                for t in set(q):
                    f = c["tf"].get(t)
                    if not f:
                        continue
                    idf = math.log(1 + (n - self.df[t] + 0.5) / (self.df[t] + 0.5))
                    s += idf * f * (k1 + 1) / (f + k1 * (1 - b + b * c["len"] / self.avg))
                if s > 0:
                    out.append((s, c))
        out.sort(key=lambda x: -x[0])
        top = out[0][0] if out else 1
        return [{"file": c["file"], "start": c["start"], "end": c["end"], "text": c["text"],
                 "score": round(s / top * 100)} for s, c in out[:k]]

    def scan(self):
        """모든 파일에서 알려진 장애 패턴을 찾아 솔루션과 함께 반환."""
        found = {}
        with self.lock:
            for name, f in self.files.items():
                for ln, line in enumerate(f["lines"], 1):
                    for r in RULES:
                        if r["re"].search(line):
                            e = found.setdefault(r["id"], {"rule": r, "count": 0, "examples": []})
                            e["count"] += 1
                            if len(e["examples"]) < 4:
                                e["examples"].append({"file": name, "line": ln, "text": line.strip()[:300]})
        return format_findings(found.values())

def format_findings(items):
    res = [{"id": e["rule"]["id"], "title": e["rule"]["title"], "severity": e["rule"]["severity"],
            "cause": e["rule"]["cause"], "solutions": e["rule"]["solutions"],
            "count": e["count"], "examples": e["examples"]} for e in items]
    res.sort(key=lambda x: (SEV_ORDER[x["severity"]], -x["count"]))
    return res

def match_rules_text(text, source):
    found = {}
    for r in RULES:
        m = r["re"].search(text)
        if m:
            found[r["id"]] = {"rule": r, "count": 1,
                              "examples": [{"file": source, "line": 0, "text": m.group(0)[:300]}]}
    return found

IDX = Index()

def load_existing():
    for p in sorted(DATA.iterdir()):
        if p.is_file():
            try:
                raw = p.read_bytes()
                IDX.files[p.name] = {"text": (t := extract_text(p.name, raw)), "lines": t.splitlines(), "size": len(raw)}
            except Exception as e:
                print("skip", p.name, e)
    IDX.rebuild()

# ---------------------------------------------------------------- AI 답변 (선택)
CFG = {"key": os.environ.get("ANTHROPIC_API_KEY", "")}   # 메모리에만 보관 (디스크 저장 안 함)
API_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/") + "/v1/messages"

def context_of(ex, radius=4):
    """탐지된 줄 주변 로그를 함께 AI 에 전달."""
    f = IDX.files.get(ex["file"])
    if not f or not ex["line"]:
        return ex["text"]
    a, b = max(0, ex["line"] - 1 - radius), ex["line"] + radius
    return "\n".join(f["lines"][a:b])

def ai_answer(query, hits, findings):
    key = CFG["key"]
    if not key:
        return None
    ctx = "\n\n".join(f"[{h['file']}:{h['start']}-{h['end']}]\n{h['text'][:1500]}" for h in hits[:5])
    fnd = "\n".join(f"- {f['title']} ({f['count']}건)" for f in findings[:6])
    prompt = (f"아래는 사용자가 업로드한 파일에서 검색된 발췌와 자동 탐지된 이슈입니다.\n"
              f"질문/증상: {query or '(없음 - 전체 파일 점검)'}\n\n탐지된 이슈:\n{fnd or '(없음)'}\n\n발췌:\n{ctx}\n\n"
              "한국어로 (1) 원인 추정 (2) 단계별 해결 방법(명령어 포함) (3) 재발 방지 순으로 간결하게 답하세요. "
              "발췌에 근거가 없는 내용은 추측임을 밝히세요.")
    body = json.dumps({"model": os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5"), "max_tokens": 1500,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(API_URL, body, {
        "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return "".join(b.get("text", "") for b in json.load(r)["content"])
    except Exception as e:
        return f"(AI 답변 실패: {e})"

# ---------------------------------------------------------------- HTTP
class H(BaseHTTPRequestHandler):
    def _json(self, obj, code=200):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path in ("/", "/index.html"):
            b = (BASE / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)
        elif u.path == "/api/files":
            self._json({"files": [{"name": n, "size": f["size"], "lines": len(f["lines"])} for n, f in IDX.files.items()],
                        "ai": bool(CFG["key"])})
        elif u.path == "/api/scan":
            self._json({"findings": IDX.scan()})
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        n = int(self.headers.get("Content-Length", 0))
        if n > MAX_BYTES:
            return self._json({"error": "파일이 너무 큽니다 (최대 20MB)"}, 413)
        body = self.rfile.read(n)
        if u.path == "/api/config":
            CFG["key"] = (json.loads(body or b"{}").get("key") or "").strip()
            return self._json({"ok": True, "ai": bool(CFG["key"])})
        if u.path == "/api/upload":
            name = os.path.basename(urllib.parse.unquote(self.headers.get("X-Filename", ""))) or "unnamed.txt"
            try:
                text = extract_text(name, body)
            except Exception as e:
                return self._json({"error": f"{name}: {e}"}, 400)
            (DATA / name).write_bytes(body)
            IDX.add(name, text, len(body))
            return self._json({"ok": True, "name": name, "lines": len(text.splitlines())})
        if u.path == "/api/search":
            q = (json.loads(body or b"{}").get("q") or "").strip()
            use_ai = bool(json.loads(body or b"{}").get("ai"))
            hits = IDX.search(q) if q else []
            found = {}
            if q:
                found.update(match_rules_text(q, "질문"))
            for h in hits[:5]:
                for rid, e in match_rules_text(h["text"], f"{h['file']}:{h['start']}").items():
                    if rid in found:
                        found[rid]["count"] += 1
                    else:
                        found[rid] = e
            findings = format_findings(found.values())
            ans = ai_answer(q, hits, findings) if use_ai else None
            return self._json({"hits": hits, "findings": findings, "ai": ans,
                               "terms": sorted(set(tokenize(q)))})
        if u.path == "/api/ai-scan":
            f = IDX.scan()
            hits = []
            for x in f[:4]:
                for ex in x["examples"][:2]:
                    hits.append({"file": ex["file"], "start": ex["line"], "end": ex["line"], "text": context_of(ex)})
            return self._json({"ai": ai_answer("", hits, f)})
        self._json({"error": "not found"}, 404)

    def do_DELETE(self):
        u = urllib.parse.urlparse(self.path)
        if u.path == "/api/files":
            name = os.path.basename(urllib.parse.parse_qs(u.query).get("name", [""])[0])
            p = DATA / name
            if name and p.is_file():
                p.unlink()
            IDX.remove(name)
            return self._json({"ok": True})
        self._json({"error": "not found"}, 404)

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    load_existing()
    print(f"DocSolver: http://localhost:{port}  (파일 {len(IDX.files)}개 로드, AI={'ON' if CFG['key'] else 'OFF'})")
    ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever()
