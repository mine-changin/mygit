#!/usr/bin/env bash
# MD 변환기 Windows 설치 파일 빌드 (Linux/macOS에서 크로스 빌드)
# 필요: go, node/npm, python3(+Pillow), makensis(NSIS 3)
# 결과: installer/out/MD-Converter-Setup.exe
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
VERSION="${VERSION:-1.0.0}"
WORK="${WORK:-$HERE/.work}"
OUT="$HERE/out"
mkdir -p "$WORK/npm" "$OUT" "$WORK/nsis"

echo "[1/4] 라이브러리 준비 (버전 고정)"
( cd "$WORK/npm" && [ -f package.json ] || npm init -y >/dev/null
  npm i --no-audit --no-fund jszip@3.10.1 turndown@7.1.2 mammoth@1.6.0 xlsx@0.18.5 pdfjs-dist@3.11.174 >/dev/null )

echo "[2/4] 앱을 오프라인용으로 변환"
rm -rf "$HERE/launcher/app" && mkdir -p "$HERE/launcher/app"
python3 "$HERE/make_app.py" "$HERE/../md-converter.html" "$WORK/npm/node_modules" "$HERE/launcher/app"

echo "[3/4] Windows 실행 파일 빌드"
( cd "$HERE/launcher" && GOOS=windows GOARCH=amd64 CGO_ENABLED=0 \
  go build -trimpath -ldflags "-H=windowsgui -s -w" -o "$WORK/nsis/md-converter.exe" . )

echo "[4/4] 설치 파일 생성"
python3 "$HERE/make_icon.py" "$WORK/nsis/app.ico"
EXE_NAME="MD-Converter-Setup.exe"
python3 - "$HERE/installer.nsi.tmpl" "$WORK/nsis/installer.nsi" "$VERSION" "$EXE_NAME" <<'PY'
import sys
t=open(sys.argv[1],encoding='utf-8').read().replace('@VERSION@',sys.argv[3]).replace('@OUT@',sys.argv[4])
open(sys.argv[2],'w',encoding='utf-8-sig').write(t)   # NSIS 유니코드: UTF-8 BOM 필요
PY
( cd "$WORK/nsis" && makensis -V2 installer.nsi && mv "$EXE_NAME" "$OUT/" )
ls -la "$OUT"
