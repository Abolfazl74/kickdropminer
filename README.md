# **KickDropMiner — Web UI Edition**

KickDropMiner automatically watches Kick livestreams and claims Drops for you.
This fully refactored miner provides a clean, modern Web UI where you can run, control, and monitor farming directly in your browser.

Now featuring **One-Click Cookie Import** — *no cookie files required!*

---

## 🚀 **Simplest Usage (Windows Package)**

The fastest way to run KickDropMiner with **zero setup**:

1. Download the latest **KickDropMiner.exe** from
   👉 [Releases](https://github.com/Abolfazl74/kickdropminer/releases)
2. Run `KickDropMiner.exe`
3. Open: **[http://localhost:8080](http://localhost:8080)**
4. Authenticate your Kick account:

   * Click the **“Authenticate”** or **“Connect Account”** button. 
   * Paste your cookies (see [**Exporting Cookies**](#exporting-cookies)) into the window. 
   * Click **Save & Connect**.

✔ **Done!** The miner starts automatically.
No Python · No installation · No manual `cookies.txt`.

---

# ✨ **Features**

* **Modern Web Dashboard**
  View progress, active campaigns, logs, and status in real time.

* **Smart Drop Farmer**
  Automatically switches streams and prioritizes unique or high-value drops.

* **One-Click Cookie Import**
  Paste your cookies directly into the UI.

* **Proxy Support**
  HTTP / HTTPS / Socks proxies supported via `config.ini`.

* **Localization System**
  Edit or add languages via `locales/*.json`.

* **Cross-Platform**
  Works on Windows, Linux, and macOS (Python version).

* **Portable Builds**
  Fully distributable executables via PyInstaller.

---

## 📸 Screenshots

### Overview
![Overview](assets/screenshots/overview.png)

<details>
<summary><strong>More Screenshots (Streamers & Console)</strong></summary>

### Streamers
![Streamers](assets/screenshots/streamers.png)

### Console
![Console](assets/screenshots/console.png)

</details>

---

# 📚 **Table of Contents**

* [Windows Usage](#-simplest-usage-windows-package)
* [Linux & Python Usage](#linux--python-usage)
* [Virtual Environment Setup](#virtual-environment-setup)
* [Exporting Cookies](#exporting-cookies)
* [Configuration & Proxy](#configuration--proxy)
* [Developer Setup](#developer-setup)
* [Running the Web UI](#running-the-web-ui)
* [Build Guide](#build-guide)
* [Troubleshooting](#troubleshooting)
* [Security & Credits](#security--credits)

---

# Linux & Python Usage

If you’re running KickDropMiner from source (Linux, macOS, or Windows without the .exe), follow these steps.

---

# Virtual Environment Setup

### 1. Clone the repository:

```sh
git clone https://github.com/Abolfazl74/kickdropminer.git
cd kickdropminer
```

### 2. Create a virtual environment:

**Linux & macOS:**

```sh
python3 -m venv .venv
source .venv/bin/activate
```

**Windows PowerShell:**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies:

```sh
pip install -r requirements.txt
```

### 4. Export your Kick cookies

(see [**Exporting Cookies**](#exporting-cookies) below)

### 5. Run the Web UI:

```sh
python webui/app.py
or
python -m webui.app
```

Then open:

```
http://localhost:8080
```

---

# Exporting Cookies

KickDropMiner requires your **Kick login session (`session_token`)**.

## 1️⃣ Install a Cookie Export Extension

Use the trusted **Get cookies.txt LOCALLY** extension:

* **Chrome / Brave / Edge**
  [https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)

* **Firefox**
  [https://addons.mozilla.org/en-US/firefox/addon/get-cookies-txt-locally/](https://addons.mozilla.org/en-US/firefox/addon/get-cookies-txt-locally/)

---

## 2️⃣ Export Your Cookies

1. Log in to **Kick.com**.
2. Click the **Get cookies.txt LOCALLY** extension icon.
3. Choose **ONE** of the following:

### **Option A — Copy to Clipboard (recommended for One-Click Import)**

* Click **Copy** / **Copy to Clipboard**
  → *You will paste this directly into the miner.*

### **Option B — Export as File (for cookies.txt users)**

* Click **Export** / **Save As**
  → Save the file as `cookies.txt`.

---

## 3️⃣ Import Into KickDropMiner

Choose one method (both work):

### ✔ **Method A — Recommended (Paste Directly in Web UI)**

1. Open the miner
2. Click **Connect Account**
3. Paste the cookie text you copied
4. Click **Save & Connect**

*No files, no paths — simplest and fastest.*

---

### ✔ **Method B — Classic cookies.txt File**

1. Take the exported cookie file
2. Make sure it is named: `cookies.txt`
3. Place it next to `KickDropMiner.exe` (or inside the project root)

The miner will load it automatically on startup.

---

# Configuration & Proxy

A `config.ini` file is created on first run.

### Proxy Example

```ini
[network]
# Format: http://user:password@ip:port OR http://ip:port
proxy = http://myuser:mypass@127.0.0.1:5000
```

### Other Settings

```ini
language = en
```

---

# Developer Setup

Already cloned and installed dependencies?
Use this to run the app during development:

```sh
python -m webui.app
```

Optionally enable debug:

```sh
python -m webui.app --debug
```

---

# Running the Web UI

After running the app:

```
http://localhost:8080
```

Use the sidebar to:

* View campaigns
* Switch streams
* Import cookies
* Reset cache
* View logs

---

# Build Guide

## Windows Build (.exe)

Install PyInstaller:

```sh
pip install pyinstaller
```

Build command:

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

Output is placed in:

```
dist/
```

---

## Linux Build (binary)

```sh
pip install pyinstaller
```

```sh
pyinstaller --onefile --name KickDropMiner --clean \
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

---

# Troubleshooting

### **“No active drops found”**

* Cookies invalid → re-export
* Campaign not live
* Use **Reset Cache** in sidebar

### **“Streamer Offline”**

* Usually syncs within 60 seconds
* Slow proxies cause delays

### **Authentication failed**

* Cookies expired
* Log out and log back in to Kick
* Export fresh cookies

### **Web UI not opening**

Try:

```
http://127.0.0.1:8080
```

Or run with debug:

```sh
python webui/app.py --debug
```

---

# Security & Credits

### Security

* Cookies are stored **locally only**
* No data is sent to external servers
* Treat cookies like passwords

### License

MIT License

### Credits

This project is fully refactored and independent.

Inspired by and thanks to:

[https://github.com/PBA4EVSKY/kickautodrops](https://github.com/PBA4EVSKY/kickautodrops)