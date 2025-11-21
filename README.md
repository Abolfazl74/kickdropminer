# KickDropMiner — Web UI Edition

KickDropMiner automatically watches Kick livestreams and claims Drops. This fully refactored miner provides a single, local Web UI that lets you run, control, and monitor the farming process in your browser.

now with **one-click cookie paste** — no files needed!

---

## 🚀 Simplest Usage (Windows Package)

**Just want to run KickDropMiner on Windows? Here’s the easiest possible way:**

1. **Download the pre-built Windows package** from [Releases](https://github.com/Abolfazl74/kickdropminer/releases) (`KickDropMiner.exe`).
2. **Double-click `KickDropMiner.exe` to start**.
3. Open [http://localhost:8080](http://localhost:8080) in your browser.
4. **Authenticate in one of two ways** (both work perfectly):
   - **Easiest (new)**: Click the "Authenticate" button → paste your Kick cookies(see [Export/Copy Cookies](#exporting-cookies) below) directly → Save & Connect
   - **Classic**: Put a valid `cookies.txt` in the same folder as the .exe (see [Export/Copy Cookies](#exporting-cookies) below)

That’s it — the miner will connect instantly with either method!

No Python or installing required.  
_If you want to customize settings, find `config.ini` in the same folder and edit as needed._

---

## Features

- Modern Web UI: Control farming, view campaign progress, logs, and claim rewards—all in one dashboard.
- Full internationalization: Easy language switching via `locales/en.json` and `config.ini`.
- Simple setup: Just Python, your Kick cookies, and you're ready.

## Table of Contents

- [🚀 Simplest Usage (Windows Package)](#simplest-usage-windows-package)
- [Requirements](#requirements)
- [Quick Setup](#quick-setup)
- [Running the Web UI](#running-the-web-ui)
- [Exporting Cookies](#exporting-cookies)
  - [Recommended Addons](#recommended-addons)
  - [Method A: cookies.txt extension](#method-a---cookiestxt-extension-recommended)
  - [Method B: browser export](#method-b-browser-extension--manual-export)
  - [Manual export: Developer Tools](#manual-export-developer-tools)
- [Configuration](#configuration)
- [Localization / UI Text](#localization--ui-text)
- [Professional Build Guide](#professional-build-guide)
  - [Windows](#windows-build)
  - [Linux](#linux-build)
  - [Packaging Executables With Example Config](#packaging-executables-with-example-config)
  - [Adding Executables to a GitHub Release](#adding-executables-to-a-github-release)
- [Troubleshooting](#troubleshooting)
- [Security Notes](#security-notes)
- [Credits & License](#credits--license)
- [Original Project Mention](#original-project-mention)

---

## Requirements

- Python **3.10+** (3.11+ highly recommended)
- Git (optional, recommended for updates)
- A valid Kick account/session (`session_token`)
- (Recommended): Python virtual environment

---

## Quick Setup

1. **Clone or download the repository:**

    ```sh
    git clone https://github.com/Abolfazl74/kickdropminer.git
    cd kickdropminer
    ```

2. **Create & activate your virtual environment:**

    ```sh
    python -m venv .venv
    # On macOS/Linux:
    source .venv/bin/activate
    # On Windows PowerShell:
    .venv\Scripts\Activate.ps1
    ```

3. **Install dependencies:**

    ```sh
    pip install -r requirements.txt
    ```

4. **Export and place your Kick cookies:**

    - see [Exporting Cookies](#exporting-cookies) below

5. **Start the Web UI:**

    ```sh
    python webui/app.py
    # or
    python -m webui.app
    ```

    Then open [http://localhost:8080](http://localhost:8080) in your browser.

---

## Exporting Cookies

You need Kick cookies (including `session_token`) in Netscape format.

### Recommended Addons
To export your Kick cookies in the proper format, use one of these official browser extensions:
- **Firefox:** [Get cookies.txt LOCALLY](https://addons.mozilla.org/en-US/firefox/addon/get-cookies-txt-locally/)
- **Chrome/Chromium:** [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)

### Method A — cookies.txt Extension (Recommended)
**Chrome & Chromium-based browsers:**
- Install the extension above.
- Log into Kick.com.
- Click the extension icon and export cookies for the site.
- Either:
  - **Copy the text** → paste directly in the app’s cookie modal (new & fastest), or
  - **Save as/Export `cookies.txt`** → name it `cookies.txt` and place it next to `KickDropMiner.exe` (classic way)

**Firefox:**
- Install the extension above.
- Log into Kick.com.
- Click the extension icon and export cookies for the site.
- Either:
  - **Copy the text** → paste directly in the app’s cookie modal (new & fastest), or
  - **Save as/Export `cookies.txt`** → name it `cookies.txt` and place it next to `KickDropMiner.exe` (classic way)

### Method B — Manual Export (Advanced)
- Use developer tools or a cookie manager.
- Export all cookies (especially `session_token`) and format correctly.
_Note: Using the extension above is much safer and easier._

---

## Configuration

- Edit settings in `config.ini` (created from `example_config.ini` on first run): change password, proxy, language, etc.
- Web UI runs on port **8080** by default.

---

## Localization / UI Text

- All interface messages are in `locales/en.json`.
- To translate or edit UI text, simply edit this file and/or add new locale files.
- Set default language in `config.ini`.

---

## Professional Build Guide

Want to make a portable executable for Windows or Linux? Here’s how:

### Windows Build

1. **Install PyInstaller:**
    ```sh
    pip install pyinstaller
    ```

2. **Build executable:**
    ```sh
    pyinstaller --onefile --console --name KickDropMiner.exe --clean ^
      --add-data "webui/templates;templates" ^
      --add-data "webui/static;static" ^
      --add-data "webui/logpipe.py;webui" ^
      --add-data "locales;locales" ^
      --add-data "core;core" ^
      --add-data "farmer.py;." ^
      --add-data "worker.py;." ^
      --add-data "example_config.ini;." ^
      --collect-all curl_cffi ^
      webui/app.py
    ```

3. **Result:** 
   Find your executable in the `dist/` folder (`KickDropMiner.exe`).  
   Copy your `cookies.txt` and `config.ini` into the same directory for a ready-to-run miner.

### Linux Build

1. **Install PyInstaller:**  
    ```sh
    pip install pyinstaller
    ```

2. **Build executable (bash syntax):**
    ```sh
    pyinstaller --onefile --console --name KickDropMiner --clean \
      --add-data "webui/templates:templates" \
      --add-data "webui/static:static" \
      --add-data "webui/logpipe.py:webui" \
      --add-data "locales:locales" \
      --add-data "core:core" \
      --add-data "farmer.py:." \
      --add-data "worker.py:." \
      --add-data "example_config.ini:." \
      --collect-all curl_cffi \
      webui/app.py
    ```

3. **Result:**  
   Your binary will appear in `dist/`.  
   Copy necessary config/cookies and launch just like the Python version.

---

## Troubleshooting

- **No campaigns detected / missing progress:**  
  Check that `cookies.txt` is present and correct. View logs in the Web UI for details.
- **SQLite errors:**  
  Use the default memory database, or ensure only one instance is running.
- **Missing campaign images:**  
  Kick API sometimes omits images; placeholders may be used.

---

## Security Notes

- Treat your `cookies.txt` file as a password—keep it safe!
- Never expose the Web UI to the public internet without authentication and HTTPS.
- Change default password before deploying on any non-localhost environment.

---

## Credits & License

Made with ♥ by StuXan and contributors  
See LICENSE file for details.

---

## Original Project Mention

This project is fully refactored and independent.  
A special thanks to the KickDropMiner repository for inspiration and reference:  
https://github.com/PBA4EVSKY/kickautodrops