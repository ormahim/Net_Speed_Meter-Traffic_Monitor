<div align="center">

# 📶 TrafficMonitor

### A tiny, private, real-time network speed meter for Windows

Live **download / upload** speed that floats on your desktop or sits right on the taskbar —
100% offline, no telemetry, no ads, no accounts. Just your numbers.

<br>

[![Platform](https://img.shields.io/badge/platform-Windows-0078D6?logo=windows&logoColor=white)](#)
[![Python](https://img.shields.io/badge/built%20with-Python-3776AB?logo=python&logoColor=white)](#)
[![Offline](https://img.shields.io/badge/network-100%25%20offline-2ea44f)](#-privacy-first)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-purple)](#)
[![Telegram](https://img.shields.io/badge/Telegram-%40ormahim-26A5E4?logo=telegram&logoColor=white)](https://t.me/ormahim)

```
↓ 1.2 MB/s
↑ 0.3 MB/s
```

</div>

<!--
  📸 TIP: add a screenshot or GIF to really sell it. Drop an image in a docs/
  folder and replace the line below, e.g.:
  ![TrafficMonitor on the taskbar](docs/screenshot.png)
-->
> 

---

## ✨ Why you might like it

- 🔒 **Truly private & offline** — it only *reads* the operating system’s network counters. It **never opens a network connection** itself. Verify it yourself in Resource Monitor.
- 🪶 **Featherweight** — a single small `.exe`, no background bloat, no installer required (one is provided if you want it).
- 🖥️ **Sits where you want** — drag it anywhere, snap it to a corner, or tuck it neatly **next to your system-tray icons**. It remembers the spot.
- 🎨 **Make it yours** — full color & font control, themes, sizes, and a transparent mode that blends into the taskbar.
- 🧩 **Open & hackable** — one readable Python file. Tweak it, rebuild it, own it.

---

## 🚀 Features

| | |
|---|---|
| ⚡ **Live up/down speed** | Refresh every **0.5 / 1 / 2 / 5 s** |
| 🔤 **System font** | Matches your real Windows UI font by default — or pick any font, **bold**/*italic* |
| 🎨 **Per-item colors** | Separate colors for background, **download ↓**, **upload ↑**, and session total |
| 🌗 **Themes** | **Auto** (follows Windows light/dark) · Dark · Light · **Transparent** |
| 📌 **Always on top** | Re-asserts itself so it’s never buried — even when it sits on the taskbar |
| 🧲 **Smart placement** | Snap to 4 corners or **left of the system tray** (nudge to clear the clock/wifi) |
| 🔔 **System-tray icon** | Lives in the notification area like IDM/Bluetooth — Show/Hide, Settings, Quit |
| 🔒 **Lock position** | Stop accidental dragging once it’s placed |
| 🎮 **Auto-hide on fullscreen** | Optionally vanish during games/videos, reappear after |
| 📐 **Units** | Auto (KB/MB) · Auto (B/KB/MB) · KB/s · MB/s · **Mbps** (like your ISP plan) |
| 🪟 **Start with Windows** | One-click toggle |
| ♻️ **Reset anytime** | Restore every setting in a click |

Everything is reachable from the **right-click menu** and a clean **Options dialog**
(right-click → *Settings…*). Your choices are saved to `config.json` next to the app.

---

## 📥 Get it

### Option A — Download a build _(no Python needed)_
Grab `TrafficMonitor.exe` (portable) or `TrafficMonitor-Setup.exe` (installer) from the
[**Releases**](../../releases) page, then just run it.

> The installer is **per-user** — no admin rights required.

### Option B — Build it yourself
You only need Python on Windows. The finished `.exe` runs anywhere with **no Python**.

```bash
# 1) clone
git clone https://github.com/ormahim/Net_Speed_Meter-Traffic_Monitor.git
cd Net_Speed_Meter-Traffic_Monitor

# 2) build (double-click build.bat, or run it)
build.bat
```

This produces `dist\TrafficMonitor.exe` (and `installer\TrafficMonitor-Setup.exe`
if [Inno Setup](https://jrsoftware.org/isdl.php) is installed).

### Option C — Run it instantly (developer mode)
```bash
pip install psutil pystray pillow
python monitor.py
```
> `pystray` + `pillow` are only for the tray icon. `pip install psutil` alone works too —
> you just won’t get the tray icon.

### Option D — Build in the cloud _(no tools on your PC)_
Push to your own GitHub repo and the included **GitHub Actions** workflow builds the
`.exe` + installer for you on a real Windows runner. Download them from the run’s artifacts.

---

## 🕹️ Using it

- **Move it** — left-click and drag anywhere (including onto the taskbar).
- **Options** — right-click the meter (or the tray icon) → everything’s there.
- **Tray icon** — right-click it for Show/Hide, Settings, About, Start-with-Windows, Quit.
- **Transparent mode** — *Theme → Transparent* makes the background see-through so only the numbers show, like it’s part of the taskbar.

---

## 🔐 Privacy first

TrafficMonitor reads the counters Windows already keeps for your network adapter
(via [`psutil`](https://pypi.org/project/psutil/)). That’s it.

- ✅ No network connections of its own
- ✅ No telemetry, analytics, or accounts
- ✅ Settings stay in a local `config.json`

Don’t take our word for it — open **Resource Monitor → Network** and confirm
`TrafficMonitor.exe` never makes a connection. You can also build the `.exe` yourself
so you trust the exact bytes, or scan it on [VirusTotal](https://www.virustotal.com/).

---

## 🛠️ Tech & project layout

| File | What it is |
|---|---|
| `monitor.py` | The whole app — a single, heavily-commented Python file |
| `make_icon.py` | Draws the app/tray icon (`icon.ico`) |
| `build.bat` | One-click local build (exe + installer) |
| `installer.iss` | Inno Setup script for the installer |
| `.github/workflows/build.yml` | Cloud build on every push |
| `BUILD.md` | Deeper build & “how to extend it” developer guide |
| `LICENSE` | MIT license |

**Built with:** Python · `tkinter` (UI) · `psutil` (counters) · `pystray` + `Pillow` (tray) · PyInstaller (packaging).

Want to extend it? `monitor.py` is split into small, clearly-named methods —
`_refresh_text`, `_build_menu`, `_show_settings`, `_apply_theme`, `_read_speeds` —
so it’s easy to find and change one thing.

---

## 🤝 Contributing

Issues, ideas, and PRs are welcome! If you build something cool on top of it
(new readouts, skins, layouts), open a PR — let’s make it better together.

1. Fork it
2. Create a branch (`git checkout -b feature/cool-thing`)
3. Commit your changes
4. Open a pull request

---

## 📨 Contact

Questions, ideas, bug reports, or just want to say hi?

- 💬 **Telegram:** [@ormahim](https://t.me/ormahim)
- 🐛 **Issues / feature requests:** use the repo’s [Issues](../../issues) tab

---

## 📝 License

Released under the **MIT License** — free to use, modify, and share, even commercially.
Just keep the copyright notice. See the [`LICENSE`](LICENSE) file for the full text.

---

<div align="center">

### ⭐ If this is useful, consider starring the repo — it really helps!

Made with ❤️ by **OR_Mahim** · [Telegram @ormahim](https://t.me/ormahim)

</div>
