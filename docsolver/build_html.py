#!/usr/bin/env python3
"""index.html + kb.py + notes.py + standalone_shim.js  ->  docsolver.html (서버 없이 더블클릭으로 실행되는 단일 파일)
kb.py / notes.py / index.html 을 수정한 뒤 `python3 build_html.py` 로 다시 빌드하세요."""
import json
from pathlib import Path

from kb import _RAW
from notes import NOTES, EXAMS, CATS

base = Path(__file__).parent
html = (base / "index.html").read_text(encoding="utf-8")
shim = (base / "standalone_shim.js").read_text(encoding="utf-8")

data = {
    "rules": [{"id": i, "re": p, "title": t, "severity": s, "cause": c, "solutions": sol}
              for (i, p, t, s, c, sol) in _RAW],
    "notes": NOTES,
    "exams": {k: {"name": v["name"], "domains": v["domains"]} for k, v in EXAMS.items()},
    "cats": CATS,
}
blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")

marker = "<script>\nconst $=s=>"
assert html.count(marker) == 1, "index.html 의 메인 스크립트 위치를 찾지 못했습니다"
html = html.replace(marker, f'<script id="ds-data" type="application/json">{blob}</script>\n<script>\n{shim}\n</script>\n{marker}')

# 단독 실행 버전에 맞는 문구
for a, b in [
    ("키는 서버 메모리에만 보관되며 저장되지 않습니다.", "키는 이 페이지 메모리에만 보관되며 저장되지 않습니다(새로고침하면 다시 입력)."),
    ("log · txt · md · conf · yaml · json · csv · docx · pdf", "log · txt · md · conf · yaml · json · csv · docx"),
    ("<title>DocSolver</title>", "<title>DocSolver (단독 실행)</title>"),
]:
    assert a in html, a
    html = html.replace(a, b)

out = base / "docsolver.html"
out.write_text(html, encoding="utf-8")
print(f"{out}  ({out.stat().st_size/1024:.0f} KB)")
