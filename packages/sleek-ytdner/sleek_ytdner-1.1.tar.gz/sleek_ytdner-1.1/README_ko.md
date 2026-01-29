# Sleek YTDner (슬릭 YTDner)

<p align="center">
  <img src="sleek_ytdner/static/images/logo.png" alt="Sleek 로고" width="150" height="auto">
</p>

<p align="center">
  <strong>Pure. Potent. Permanent.</strong><br>
  타협하지 않는 완벽주의자를 위해 설계된 마지막 미디어 아카이버.
</p>

<p align="center">
  <a href="LICENSE_ko.md"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="라이선스"></a>
  <img src="https://img.shields.io/badge/Python-3.12%2B-blue" alt="Python 버전">
  <img src="https://img.shields.io/badge/PyPI-v1.1-orange" alt="PyPI">
  <img src="https://img.shields.io/badge/Docker-GHCR-blue" alt="Docker">
</p>

---
[English](README.md) | [한국어](README_ko.md)
---

## 📖 소개

**Sleek YTDner**는 현대적이고 미니멀한 유튜브 다운로더이자 미디어 아카이버입니다. **Flask**를 기반으로 강력한 **yt-dlp** 엔진을 활용하며, 모든 기능을 아름다운 고성능 글래스모피즘(Glassmorphism) UI로 제공합니다.

## 🚀 설치 및 시작하기

원하는 환경에 맞춰 Sleek YTDner를 사용해 보세요:

### 1. 무설치 실행 파일 (가장 간편한 방법)
파이썬 설치 없이 [최신 릴리즈](https://github.com/hslcrb/pypack_sleek_a-ytdownloader-pkg/releases)에서 OS별 실행 파일을 다운로드하세요.

*   **Windows**: `sleek-downloader-v1.0-windows.zip` 다운로드 후 압축을 풀고 `sleek-downloader.exe` 실행.
*   **macOS**: `sleek-downloader-v1.0-macos.zip` 다운로드 후 압축을 풀고 `sleek-downloader` 실행.
*   **Linux**: `sleek-downloader-v1.0-linux.zip` 다운로드 후 압축을 풀고 `./sleek-downloader` 실행.

### 2. 터미널 즉시 설치 (PyPI)
파이썬이 설치되어 있다면, 명령줄 한 줄로 즉시 설치하고 실행할 수 있습니다:
```bash
pip install sleek-ytdner
sleek-downloader
```

### 3. 도커 (Docker)
시스템에 아무것도 설치하지 않고 컨테이너로 실행하세요:
```bash
docker pull ghcr.io/hslcrb/pypack_sleek_a-ytdownloader-pkg:v1.1
docker run -p 5000:5000 -v $(pwd)/downloads:/data/downloads ghcr.io/hslcrb/pypack_sleek_a-ytdownloader-pkg:v1.1
```

## 🛠️ 필수 조건 (파이썬/소스 설치 시)

- **Python 3.8+**
- **FFmpeg**: 고화질 영상/음원 병합을 위해 필수입니다.
  - *Ubuntu/Debian*: `sudo apt install ffmpeg`
  - *macOS*: `brew install ffmpeg`
  - *Windows*: [FFmpeg.org](https://ffmpeg.org/)에서 다운로드 후 PATH에 추가.

## 💻 사용 방법

어떤 방식으로든 서버를 실행한 후:
1. 웹 브라우저에서 `http://localhost:5000` 접속.
2. 유튜브 URL 붙여넣기.
3. 화질 선택 후 다운로드.

앱은 실행된 현재 디렉토리에 `config.json` 설정 파일과 `downloads` 폴더를 자동으로 생성합니다.

## 📄 라이선스
MIT License - © 2008-2026 Rheehose (Rhee Creative).

---
<p align="center">
  <em>최종 업데이트: 2026년 1월 17일 (KST)</em>
</p>
