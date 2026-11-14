#!/usr/bin/env python3
"""md-converter.html 을 오프라인(설치형) 앱으로 변환한다.
- CDN 스크립트 → 내장 lib/ 파일
- 구글 폰트 링크 제거, 시스템 한글 글꼴 우선
- PDF 한글 CMap 사용(cMapUrl), 창 닫힘 감지용 하트비트 추가
사용: make_app.py <원본html> <npm_modules> <출력디렉터리>
"""
import os, re, shutil, sys

src, nm, out = sys.argv[1:4]
html = open(src, encoding='utf-8').read()

libs = {
 'https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js': ('jszip/dist/jszip.min.js', 'jszip.min.js'),
 'https://cdnjs.cloudflare.com/ajax/libs/turndown/7.1.2/turndown.min.js': ('turndown/lib/turndown.browser.umd.js', 'turndown.min.js'),
 'https://cdnjs.cloudflare.com/ajax/libs/mammoth/1.6.0/mammoth.browser.min.js': ('mammoth/mammoth.browser.min.js', 'mammoth.browser.min.js'),
 'https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js': ('xlsx/dist/xlsx.full.min.js', 'xlsx.full.min.js'),
 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js': ('pdfjs-dist/build/pdf.min.js', 'pdf.min.js'),
 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js': ('pdfjs-dist/build/pdf.worker.min.js', 'pdf.worker.min.js'),
}
os.makedirs(os.path.join(out, 'lib'), exist_ok=True)
for url, (rel, name) in libs.items():
    assert url in html, url
    html = html.replace(url, 'lib/' + name)
    shutil.copy(os.path.join(nm, rel), os.path.join(out, 'lib', name))
cm = os.path.join(out, 'lib', 'cmaps')
if os.path.isdir(cm): shutil.rmtree(cm)
shutil.copytree(os.path.join(nm, 'pdfjs-dist', 'cmaps'), cm)

# 구글 폰트 링크 제거 + 시스템 글꼴
html, n = re.subn(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^>]*>\n?', '', html)
assert n == 1
html = html.replace("--font-ui:'Noto Sans KR',", "--font-ui:'Noto Sans KR','Malgun Gothic','맑은 고딕',", 1)
html = html.replace("--font-mono:'JetBrains Mono',", "--font-mono:'JetBrains Mono',Consolas,'D2Coding',", 1)

# PDF: 한글 CMap
a = "pdfjsLib.getDocument({data:new Uint8Array(buf)})"
assert a in html
html = html.replace(a, "pdfjsLib.getDocument({data:new Uint8Array(buf),cMapUrl:'lib/cmaps/',cMapPacked:true})", 1)

# 하트비트 (런처가 창이 닫히면 스스로 종료)
hb = """<script>
(function(){function p(){try{fetch('__ping',{cache:'no-store'}).catch(function(){})}catch(e){}}
p();setInterval(p,5000);
window.addEventListener('pagehide',function(){try{navigator.sendBeacon('__bye')}catch(e){}});
window.addEventListener('pageshow',p);})();
</script>
"""
i = html.rindex('</script>') + len('</script>')
html = html[:i] + '\n' + hb + html[i:]
assert '__ping' in html
open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(html)
print('앱 변환 완료:', out)
