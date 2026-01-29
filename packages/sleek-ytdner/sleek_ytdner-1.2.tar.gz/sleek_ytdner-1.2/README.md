# Sleek YTDner

<p align="center">
  <img src="https://raw.githubusercontent.com/hslcrb/pypack_sleek_a-ytdownloader-pkg/main/sleek_ytdner/static/images/logo.png" alt="Sleek Logo" width="150" height="auto">
</p>

<p align="center">
  <strong>Pure. Potent. Permanent.</strong><br>
  The last media archiver designed for the uncompromising perfectionist.
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License"></a>
  <img src="https://img.shields.io/badge/Python-3.12%2B-blue" alt="Python Version">
  <img src="https://img.shields.io/badge/PyPI-v1.2-orange" alt="PyPI">
  <img src="https://img.shields.io/badge/Docker-GHCR-blue" alt="Docker">
</p>

---
[English](README.md) | [한국어](README_ko.md)
---

## 📖 Introduction

**Sleek YTDner** is a modern, minimalist YouTube downloader and media archiver. Built with **Flask** and powered by the robust **yt-dlp** engine, it wraps powerful functionality in a stunning, high-performance Glassmorphism UI.

## 🚀 Installation & Setup

Choose your preferred way to use Sleek YTDner:

### 1. Direct Executable (No Python Required)
Download the standalone executable for your OS from the [Latest Releases](https://github.com/hslcrb/pypack_sleek_a-ytdownloader-pkg/releases).

*   **Windows**: Download `sleek-downloader-v1.0-windows.zip`, extract, and run `sleek-downloader.exe`.
*   **macOS**: Download `sleek-downloader-v1.0-macos.zip`, extract, and run `sleek-downloader`.
*   **Linux**: Download `sleek-downloader-v1.0-linux.zip`, extract, and run `./sleek-downloader`.

### 2. Fast Terminal Install (Via PyPI)
If you have Python installed, you can install Sleek YTDner instantly:
```bash
pip install sleek-ytdner
sleek-downloader
```

### 3. Docker (Containerized)
Run Sleek YTDner without installing anything on your host system:
```bash
docker pull ghcr.io/hslcrb/pypack_sleek_a-ytdownloader-pkg:v1.2
docker run -p 5000:5000 -v $(pwd)/downloads:/data/downloads ghcr.io/hslcrb/pypack_sleek_a-ytdownloader-pkg:v1.2
```

## 🛠️ Prerequisites (For Python/Source Install)

- **Python 3.8+**
- **FFmpeg**: Required for high-quality merging.
  - *Ubuntu/Debian*: `sudo apt install ffmpeg`
  - *macOS*: `brew install ffmpeg`
  - *Windows*: Download from [FFmpeg.org](https://ffmpeg.org/).

## 💻 Usage

Once launched via any method:
1. Open your browser to `http://localhost:5000`.
2. Paste a YouTube URL.
3. Choose quality and download.

The application automatically creates a `config.json` and a `downloads` folder in your current directory.

## 📄 License
MIT License - © 2008-2026 Rheehose (Rhee Creative).

---
<p align="center">
  <em>Last Updated: 2026-01-17 (KST)</em>
</p>
