<div align="center">
  <img src="assets/icon.png" width="128" alt="VidMuncher Logo">

# VidMuncher

**A Video Downloader Born from Pure Frustration**

[![Made by Non-Developer](https://img.shields.io/badge/Made%20by-Non--Developer-red.svg)]() [![Downloads](https://img.shields.io/github/downloads/aprixlabs/VidMuncher/total.svg?color=brightgreen&label=Downloads)]()

</div>

I built this because a certain multi-billion dollar video editor throws a tantrum over unsupported codecs. I'm not a real developer, but out of pure, unadulterated spite, I accidentally engineered a hardware-accelerated, self-updating media devouring monster. It was supposed to be a simple 10-line script. Now it has transcode support and a GUI. Please use it so my suffering isn't in vain.

## What It Does

- **Downloads videos** from YouTube and 1000+ other sites via yt-dlp. [View yt-dlp Supported sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)
- **Encodes to H.264, H.265, or AV1** — NVIDIA, AMD, Intel QuickSync, or CPU. Falls back silently if your GPU refuses to cooperate
- **Audio extraction** for when you just want the audio
- **Self-configuring** — downloads yt-dlp and FFmpeg automatically on first launch. No manual setup required
- **Updater** — keeps the App, yt-dlp and FFmpeg current

## Getting Started

### Executable (Recommended)
1. Download the latest release
2. Extract and run `VidMuncher.exe`
3. It sets itself up. You're done.

> **⚠️ Windows SmartScreen Warning**
> Because this is an indie, open-source project without a paid Code Signing Certificate, Windows SmartScreen may flag the `.exe` as an "unrecognized app". This is completely normal.
> To run VidMuncher, click **"More info"** -> **"Run anyway"**.

### From Source
```bash
git clone https://github.com/aprixlabs/VidMuncher.git
cd VidMuncher
pip install -r requirements.txt
python vidmuncher.py
```

### Build Executable
```bash
python build_vidmuncher.py

# Clean build artifacts
python build_vidmuncher.py clean
```

## Legal

Personal use only. Don't download things you shouldn't. [GPL-3.0 License](LICENSE).

## Thanks To

- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** — for doing the actual hard part
- **[FFmpeg](https://ffmpeg.org)** — for doing the other actual hard part
- **My video editor** — for being so picky about codecs that I had to build this
