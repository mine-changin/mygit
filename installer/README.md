# MD 변환기 Windows 설치 파일

`./build.sh` 실행 → `out/MD-Converter-Setup.exe` 생성 (Linux/macOS에서 크로스 빌드).
필요: go, node/npm, python3 + Pillow, makensis(NSIS 3). 버전은 `VERSION=1.0.1 ./build.sh`.

- 설치형 앱은 `../md-converter.html` 을 그대로 사용하며, CDN 대신 라이브러리를 내장합니다(오프라인 동작).
- `launcher/` : 127.0.0.1 에서만 앱을 서비스하는 Go 런처. Edge 앱 창(없으면 기본 브라우저)으로 열고, 창을 닫으면 종료.
- 설치 위치: `%LOCALAPPDATA%\Programs\MDConverter` (관리자 권한 불필요), 시작 메뉴/바탕화면 바로가기, 제어판 제거 등록.
- 서명되지 않은 파일이라 Windows SmartScreen 경고가 나올 수 있습니다.
