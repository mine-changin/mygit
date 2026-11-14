/* DocSolver 단독 실행용: server.py 의 /api/* 를 브라우저 안에서 구현한다. (build_html.py 가 index.html 에 주입)
   - 파일은 이 브라우저의 IndexedDB 에만 저장되며 외부로 전송되지 않는다 (AI 분석을 켠 경우 제외). */
(() => {
const D = JSON.parse(document.getElementById('ds-data').textContent);
const RULES = D.rules.map(r => ({...r, rx: new RegExp(r.re, 'i')}));
const SEV = {high: 0, medium: 1, low: 2};
const _fetch = window.fetch.bind(window);
const CFG = {key: ''};
const MAX_BYTES = 20 * 1024 * 1024, CHUNK_LINES = 14, OVERLAP = 3, CHUNK_CHARS = 1400;

/* 줄 분리: 파일 끝 개행 뒤의 빈 줄은 제외 (Python str.splitlines 와 동일) */
const splitLines = t => { const a = t.split(/\r?\n/); if (a.length && a[a.length - 1] === '') a.pop(); return a; };

/* ---------- 토크나이저 / BM25 ---------- */
function tokenize(t) {
  t = t.toLowerCase();
  const out = t.match(/[a-z0-9_]+/g) || [];
  for (const w of (t.match(/[가-힣]+/g) || [])) {
    if (w.length === 1) out.push(w);
    else for (let i = 0; i < w.length - 1; i++) out.push(w.slice(i, i + 2));
  }
  return out;
}
const counter = a => { const m = new Map(); for (const x of a) m.set(x, (m.get(x) || 0) + 1); return m; };
function bm25(tf, len, qset, N, df, avg, k1, b) {
  let s = 0;
  for (const t of qset) {
    const f = tf.get(t); if (!f) continue;
    const d = df.get(t) || 0, idf = Math.log(1 + (N - d + 0.5) / (d + 0.5));
    s += idf * f * (k1 + 1) / (f + k1 * (1 - b + b * len / avg));
  }
  return s;
}

/* ---------- 업로드 파일 인덱스 ---------- */
const files = new Map();
let chunks = [], df = new Map(), avg = 1;
function rebuild() {
  chunks = []; df = new Map();
  for (const [name, f] of files) {
    const lines = f.lines; let i = 0;
    while (i < lines.length) {
      let j = i, size = 0;
      while (j < lines.length && (j - i < CHUNK_LINES) && size < CHUNK_CHARS) { size += lines[j].length + 1; j++; }
      j = Math.max(j, i + 1);
      const text = lines.slice(i, j).join('\n'), toks = tokenize(text);
      chunks.push({file: name, start: i + 1, end: j, text, tf: counter(toks), len: toks.length || 1});
      if (j >= lines.length) break;
      i = Math.max(j - OVERLAP, i + 1);
    }
  }
  for (const c of chunks) for (const k of c.tf.keys()) df.set(k, (df.get(k) || 0) + 1);
  avg = chunks.length ? chunks.reduce((a, c) => a + c.len, 0) / chunks.length : 1;
}
function search(q, k = 8) {
  const qs = new Set(tokenize(q)); if (!qs.size) return [];
  const out = [];
  for (const c of chunks) { const s = bm25(c.tf, c.len, qs, chunks.length, df, avg, 1.5, 0.75); if (s > 0) out.push([s, c]); }
  out.sort((a, b) => b[0] - a[0]);
  const top = out.length ? out[0][0] : 1;
  return out.slice(0, k).map(([s, c]) => ({file: c.file, start: c.start, end: c.end, text: c.text, score: Math.round(s / top * 100)}));
}

/* ---------- 장애 패턴 탐지 ---------- */
function fmtFindings(items) {
  const r = items.map(e => ({id: e.rule.id, title: e.rule.title, severity: e.rule.severity, cause: e.rule.cause,
    solutions: e.rule.solutions, count: e.count, examples: e.examples}));
  r.sort((a, b) => SEV[a.severity] - SEV[b.severity] || b.count - a.count);
  return r;
}
function scan() {
  const found = new Map();
  for (const [name, f] of files) f.lines.forEach((line, idx) => {
    for (const r of RULES) if (r.rx.test(line)) {
      let e = found.get(r.id);
      if (!e) { e = {rule: r, count: 0, examples: []}; found.set(r.id, e); }
      e.count++;
      if (e.examples.length < 4) e.examples.push({file: name, line: idx + 1, text: line.trim().slice(0, 300)});
    }
  });
  return fmtFindings([...found.values()]);
}
function matchText(text, src) {
  const f = new Map();
  for (const r of RULES) { const m = text.match(r.rx); if (m) f.set(r.id, {rule: r, count: 1, examples: [{file: src, line: 0, text: m[0].slice(0, 300)}]}); }
  return f;
}

/* ---------- CKA/CKAD 노트 ---------- */
const NDOCS = D.notes.map(n => {
  const text = (n.title + ' ').repeat(3) + (n.tags.join(' ') + ' ').repeat(2) + n.body;
  const toks = tokenize(text);
  return {n, tf: counter(toks), len: toks.length || 1, low: text.toLowerCase()};
});
const NDF = new Map();
for (const d of NDOCS) for (const k of d.tf.keys()) NDF.set(k, (NDF.get(k) || 0) + 1);
const NAVG = NDOCS.reduce((a, d) => a + d.len, 0) / NDOCS.length;
function searchNotes(q, exam, cat) {
  let pool = NDOCS.filter(d => !exam || d.n.exams.includes(exam));
  const cats = new Map(); for (const d of pool) cats.set(d.n.cat, (cats.get(d.n.cat) || 0) + 1);
  pool = pool.filter(d => !cat || d.n.cat === cat);
  q = q.trim();
  if (!q) return [pool.map(d => [d.n, null]), cats];
  const qs = new Set(tokenize(q)), out = [];
  for (const d of pool) {
    let s = bm25(d.tf, d.len, qs, NDOCS.length, NDF, NAVG, 1.4, 0.75);
    if (d.low.includes(q.toLowerCase())) s += 2.0;
    if (s > 0) out.push([s, d.n]);
  }
  out.sort((a, b) => b[0] - a[0]);
  const top = out.length ? out[0][0] : 1;
  return [out.map(([s, n]) => [n, Math.round(s / top * 100)]), cats];
}

/* ---------- AI 분석 (브라우저에서 Anthropic API 직접 호출) ---------- */
function ctxOf(ex, radius = 4) {
  const f = files.get(ex.file);
  if (!f || !ex.line) return ex.text;
  return f.lines.slice(Math.max(0, ex.line - 1 - radius), ex.line + radius).join('\n');
}
async function aiAnswer(query, hits, findings) {
  if (!CFG.key) return null;
  const ctx = hits.slice(0, 5).map(h => `[${h.file}:${h.start}-${h.end}]\n${h.text.slice(0, 1500)}`).join('\n\n');
  const fnd = findings.slice(0, 6).map(f => `- ${f.title} (${f.count}건)`).join('\n');
  const prompt = `아래는 사용자가 업로드한 파일에서 검색된 발췌와 자동 탐지된 이슈입니다.\n질문/증상: ${query || '(없음 - 전체 파일 점검)'}\n\n탐지된 이슈:\n${fnd || '(없음)'}\n\n발췌:\n${ctx}\n\n` +
    '한국어로 (1) 원인 추정 (2) 단계별 해결 방법(명령어 포함) (3) 재발 방지 순으로 간결하게 답하세요. 발췌에 근거가 없는 내용은 추측임을 밝히세요.';
  try {
    const r = await _fetch('https://api.anthropic.com/v1/messages', {method: 'POST',
      headers: {'x-api-key': CFG.key, 'anthropic-version': '2023-06-01', 'content-type': 'application/json',
                'anthropic-dangerous-direct-browser-access': 'true'},
      body: JSON.stringify({model: 'claude-sonnet-5-5', max_tokens: 1500, messages: [{role: 'user', content: prompt}]})});
    const j = await r.json();
    if (!r.ok) throw new Error((j.error && j.error.message) || r.status);
    return j.content.map(b => b.text || '').join('');
  } catch (e) { return `(AI 답변 실패: ${e.message})`; }
}

/* ---------- 파일 읽기 ---------- */
async function docx(buf) {
  const dv = new DataView(buf), u8 = new Uint8Array(buf);
  let e = u8.length - 22; while (e >= 0 && dv.getUint32(e, true) !== 0x06054b50) e--;
  if (e < 0) throw new Error('docx 형식 오류');
  const n = dv.getUint16(e + 10, true); let p = dv.getUint32(e + 16, true);
  for (let i = 0; i < n; i++) {
    const method = dv.getUint16(p + 10, true), csz = dv.getUint32(p + 20, true), nl = dv.getUint16(p + 28, true),
          xl = dv.getUint16(p + 30, true), cl = dv.getUint16(p + 32, true), lo = dv.getUint32(p + 42, true);
    if (new TextDecoder().decode(u8.subarray(p + 46, p + 46 + nl)) === 'word/document.xml') {
      const start = lo + 30 + dv.getUint16(lo + 26, true) + dv.getUint16(lo + 28, true), data = u8.subarray(start, start + csz);
      const xml = method === 0 ? new TextDecoder().decode(data)
        : await new Response(new Blob([data]).stream().pipeThrough(new DecompressionStream('deflate-raw'))).text();
      return xml.replace(/<\/w:p>/g, '\n').replace(/<[^>]+>/g, '').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
    }
    p += 46 + nl + xl + cl;
  }
  throw new Error('docx 본문을 찾을 수 없습니다');
}
async function extract(name, buf) {
  const ext = name.split('.').pop().toLowerCase();
  if (ext === 'docx') return docx(buf);
  if (ext === 'pdf') throw new Error('PDF 는 HTML 단독 버전에서 지원하지 않습니다 (서버 버전 + pypdf 사용).');
  const u8 = new Uint8Array(buf);
  if (u8.subarray(0, 4096).includes(0)) throw new Error('지원하지 않는 바이너리 파일입니다.');
  try { return new TextDecoder('utf-8', {fatal: true}).decode(u8).replace(/^﻿/, ''); }
  catch { try { return new TextDecoder('euc-kr').decode(u8); } catch { return new TextDecoder('latin1').decode(u8); } }
}

/* ---------- IndexedDB 저장 ---------- */
const dbp = new Promise(res => {
  try {
    const rq = indexedDB.open('docsolver', 1);
    rq.onupgradeneeded = () => rq.result.createObjectStore('files', {keyPath: 'name'});
    rq.onsuccess = () => res(rq.result); rq.onerror = () => res(null);
  } catch { res(null); }
});
const dbAll = async () => { const db = await dbp; if (!db) return [];
  return new Promise(r => { const q = db.transaction('files').objectStore('files').getAll(); q.onsuccess = () => r(q.result); q.onerror = () => r([]); }); };
const dbPut = async rec => { const db = await dbp; if (db) db.transaction('files', 'readwrite').objectStore('files').put(rec); };
const dbDel = async name => { const db = await dbp; if (db) db.transaction('files', 'readwrite').objectStore('files').delete(name); };
const ready = (async () => {
  for (const r of await dbAll()) files.set(r.name, {lines: splitLines(r.text), size: r.size});
  rebuild();
})();

/* ---------- /api/* 라우터 ---------- */
const J = (o, s = 200) => new Response(JSON.stringify(o), {status: s, headers: {'content-type': 'application/json'}});
window.fetch = async (url, init = {}) => {
  if (typeof url !== 'string' || !url.startsWith('/api/')) return _fetch(url, init);
  await ready;
  const u = new URL(url, 'http://x'), method = (init.method || 'GET').toUpperCase(), path = u.pathname;
  const body = () => { try { return JSON.parse(init.body || '{}'); } catch { return {}; } };

  if (path === '/api/files' && method === 'GET')
    return J({files: [...files].map(([name, f]) => ({name, size: f.size, lines: f.lines.length})), ai: !!CFG.key});
  if (path === '/api/files' && method === 'DELETE') {
    const name = u.searchParams.get('name') || '';
    files.delete(name); await dbDel(name); rebuild(); return J({ok: true});
  }
  if (path === '/api/config') { CFG.key = (body().key || '').trim(); return J({ok: true, ai: !!CFG.key}); }
  if (path === '/api/scan') return J({findings: scan()});
  if (path === '/api/upload') {
    const h = init.headers || {};
    const name = decodeURIComponent(h['X-Filename'] || '').split(/[\\/]/).pop() || 'unnamed.txt';
    const buf = await init.body.arrayBuffer();
    if (buf.byteLength > MAX_BYTES) return J({error: '파일이 너무 큽니다 (최대 20MB)'}, 413);
    let text; try { text = await extract(name, buf); } catch (e) { return J({error: `${name}: ${e.message}`}, 400); }
    files.set(name, {lines: splitLines(text), size: buf.byteLength});
    await dbPut({name, text, size: buf.byteLength}); rebuild();
    return J({ok: true, name, lines: files.get(name).lines.length});
  }
  if (path === '/api/search') {
    const b = body(), q = (b.q || '').trim(), hits = q ? search(q) : [];
    const found = new Map();
    if (q) for (const [k, v] of matchText(q, '질문')) found.set(k, v);
    for (const h of hits.slice(0, 5)) for (const [k, v] of matchText(h.text, `${h.file}:${h.start}`)) {
      if (found.has(k)) found.get(k).count++; else found.set(k, v);
    }
    const findings = fmtFindings([...found.values()]);
    const ai = b.ai ? await aiAnswer(q, hits, findings) : null;
    return J({hits, findings, ai, terms: [...new Set(tokenize(q))].sort()});
  }
  if (path === '/api/ai-scan') {
    const f = scan(), hits = [];
    for (const x of f.slice(0, 4)) for (const ex of x.examples.slice(0, 2))
      hits.push({file: ex.file, start: ex.line, end: ex.line, text: ctxOf(ex)});
    return J({ai: await aiAnswer('', hits, f)});
  }
  if (path === '/api/notes') {
    const q = u.searchParams.get('q') || '', exam = D.exams[u.searchParams.get('exam')] ? u.searchParams.get('exam') : '',
          cat = u.searchParams.get('cat') || '';
    const [found, cats] = searchNotes(q, exam, cat);
    const mine = q.trim() && files.size ? search(q, 4) : [];
    return J({notes: found.map(([n, sc]) => ({id: n.id, title: n.title, exams: n.exams, cat: n.cat, body: n.body, score: sc})),
      mine, terms: [...new Set(tokenize(q))].sort(),
      meta: {cats: D.cats.filter(c => cats.get(c)).map(c => ({name: c, count: cats.get(c)})), exams: D.exams, total: D.notes.length}});
  }
  return J({error: 'not found'}, 404);
};
})();
