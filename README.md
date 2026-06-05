# TrafficMonitor — private real-time network speed meter  ·  v1.0.0

A tiny always-on-top widget showing your live **download / upload** speed.
Built to be 100% offline and fully yours — no telemetry, no ads, no mystery code.

> Shows e.g.  `↓ 1.2 MB/s   ↑ 0.3 MB/s`

## Features
- Live up/down speed; refresh rate **0.5 / 1 / 2 / 5 s**
- **System-tray icon** — sits in the notification area / hidden-icons flyout
  (like IDM or Bluetooth); right-click it to Show/Hide, open Settings, or Quit
- Uses your **actual Windows system font** by default (or pick any font)
- **Drag anywhere** (incl. onto the taskbar) — remembers the spot across reboots
- **Stays on top reliably** — re-asserts itself each refresh so it no longer
  gets buried behind an app you just opened (even when it sits on the taskbar)
- **Snap**: 4 corners, or **Left of system tray** (+ nudge left/right to sit just before the wifi icon)
- Themes: **Auto** (matches Windows light/dark), **Dark**, **Light**, **Transparent** (see-through, only text shows; text stays readable on any taskbar)
- **Options dialog** (right-click → *Settings…*), like the original TrafficMonitor:
  - **Taskbar window settings** — full **per-item colors** (background, download ↓, upload ↑, session total ∑) + **font** family / size / **bold** / *italic* + an **arrow↔number gap** control
  - **General settings** — **Lock window position**, **Always on top**, **Hide main window when a program is fullscreen**, **Show tray icon** (each a ✔ checkbox)
- **Size** presets (Small/Medium/Large/XL) so the box height matches your taskbar
- **Units**: Auto (KB/MB, no B/s), Auto (B/KB/MB), KB/s, MB/s, or Mbps (like your ISP)
- **Start with Windows** toggle · optional session data total
- **Right-click menu shows ✔ ticks / dots** on the currently-selected option
- **Reset all settings** in one click
- **Never makes a network connection** — it only reads OS counters

All options are in the **right-click menu** (quick toggles), the **tray icon**,
and the **Settings…** dialog. Choices save to `config.json` (next to the app).

## Dependencies
- **`psutil`** — required (reads the OS network counters).
- **`pystray` + `Pillow`** — optional, only for the **tray icon**. If they're
  missing the app still runs fine; it just won't show a tray icon.

---

## Getting the app — pick ONE

### 🟢 Option A — Cloud build (no Python, no tools on your PC) — recommended
1. Put this folder in a **GitHub repo** (it can be **private**).
2. Open the repo's **Actions** tab → run **"Build Windows exe + installer"** (or just push).
3. Download the **TrafficMonitor** artifact → it has both:
   - `TrafficMonitor.exe` (portable — just run it)
   - `TrafficMonitor-Setup.exe` (the one-click installer)

GitHub is used *only* to compile your own code. Nothing is published.

### 🔵 Option B — Build once on any PC that has Python
Run **`build.bat`** (double-click). It makes `dist\TrafficMonitor.exe`, and also
`installer\TrafficMonitor-Setup.exe` if [Inno Setup](https://jrsoftware.org/isdl.php)
is installed. Then copy those files to any Windows PC — **they need no Python to run**.

### Just try it instantly (developer mode)
```
pip install psutil pystray pillow
python monitor.py
```
(`pystray`/`pillow` are only for the tray icon — `pip install psutil` alone
also works, you just won't get the tray icon.)

> ⚠️ PyInstaller can't cross-compile — a **Windows** .exe must be built **on Windows**
> (your PC, a friend's, or the free cloud option above).

---

## Installing (the Setup.exe)
Double-click `TrafficMonitor-Setup.exe` → it installs **per-user (no admin needed)**,
adds a Start-menu shortcut, and offers optional desktop icon + start-with-Windows.
Uninstall anytime from **Settings → Apps**.

---

## Change / extend it later
Open `monitor.py`. The top `DEFAULT_CONFIG` block has every setting commented.
Entry points for new features:

| Want to… | Edit this method |
|---|---|
| Add a setting | `DEFAULT_CONFIG` (top of file) |
| Change what text is shown | `_refresh_text()` |
| Add a right-click menu item | `_build_menu()` |
| Add a row to the Options dialog | `_show_settings()` |
| Change how speed is measured | `_read_speeds()` |
| Change colors / themes | `_apply_theme()` |
| Change sizes | `SIZE_PRESETS` (top of file) |
| Change the tray icon / menu | `make_icon.py` + `_build_tray()` |

Hand the file to any AI and point it at the right method.

## Security notes
- Dependencies: `psutil` (required) and `pystray` + `Pillow` (only for the
  tray icon) — plus Python's built-ins.
- Build it yourself (locally or in *your* GitHub) so you trust the exact exe.
- Prove it's offline: open **Resource Monitor → Network** and confirm
  `TrafficMonitor.exe` never shows network activity.
- Optional: scan the built exe at <https://virustotal.com>.
