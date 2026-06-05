"""
TrafficMonitor - a tiny, private real-time network speed meter for Windows.

A borderless always-on-top widget that shows your live download / upload speed.
  - Drag it anywhere (including onto the taskbar) -> it remembers the spot.
  - Right-click it for ALL options (snap, refresh rate, theme, settings, quit).
  - Right-click -> "Settings..." opens a full Options dialog (colors + font).
  - Matches your Windows light/dark theme automatically.
  - 100% offline: this app NEVER makes a network connection. It only *reads* counters.

================================================================================
 HOW TO CHANGE THINGS LATER  (this is the only section you usually need to touch)
================================================================================
Every setting lives in DEFAULT_CONFIG just below. Change a value, save, re-run.
They are ALSO changeable at runtime from the right-click menu / the Options
dialog, and whatever you pick is saved to "config.json" (created next to this
file / the .exe) so it sticks across reboots.

If you (or an AI/expert helping you) want to ADD a feature later:
  * New setting?            -> add a key to DEFAULT_CONFIG with a comment.
  * New display item?       -> edit the _refresh_text() method.
  * New menu option?        -> edit the _build_menu() method.
  * New Options-dialog row?  -> edit the _show_settings() method.
  * Change the tray icon/menu -> edit make_icon.py + the _build_tray() method.
  * Change how speed reads  -> edit _read_speeds().
  * Change colors / themes  -> edit _apply_theme().
The code is split into small, clearly-named methods on purpose so each piece is
easy to find and swap out.
================================================================================
"""

import json
import os
import queue
import sys
import time
import tkinter as tk
from tkinter import ttk, colorchooser

import psutil  # the ONLY required third-party dependency. `pip install psutil`

# winreg + ctypes are Windows-only standard-library modules. We guard the import
# so the file can still be opened/inspected on other systems without crashing.
try:
    import winreg
except ImportError:
    winreg = None

try:
    import ctypes
    from ctypes import wintypes
except Exception:   # ImportError on most OSes, ValueError for wintypes on Linux
    ctypes = None
    wintypes = None

# Optional: the system-tray icon (so the app sits in the notification area /
# hidden-icons flyout, like IDM or Bluetooth). Needs `pystray` + `Pillow`.
# If they're missing the app still runs fine -- it just has no tray icon.
try:
    import pystray
    from make_icon import make_image
except Exception:
    pystray = None
    make_image = None


APP_NAME = "TrafficMonitor"      # used for the autostart registry entry + title
APP_VERSION = "1.0.0"            # shown in the title, menu, About and Options


# =============================================================================
#  CONFIG  -- edit these defaults freely. Comments show valid options.
# =============================================================================
DEFAULT_CONFIG = {
    # How often the numbers update, in seconds. Try: 0.5, 1, 2, 5
    "refresh_seconds": 1.0,

    # How speeds are shown:
    #   "auto"    -> B/s, KB/s, MB/s (whatever fits) -- can show B/s when idle
    #   "autokb"  -> KB/s, MB/s only (never B/s; idle shows "0 KB/s")
    #   "KBps"    -> always KB/s
    #   "MBps"    -> always megabytes/sec
    #   "Mbps"    -> megabits/sec (like your ISP plan, e.g. "100 Mbps")
    "units": "autokb",

    # Color theme:
    #   "auto"        -> follow Windows light/dark automatically
    #   "dark"/"light"-> force that look
    #   "transparent" -> see-through background, only the text shows
    #                    (looks like it's part of the taskbar)
    "theme": "auto",

    # Stay above other windows (re-asserted every refresh so it never gets
    # buried behind an app you just opened -- even when it sits on the taskbar).
    "always_on_top": True,

    # Lock the position so you can't drag it by accident.
    "lock_position": False,

    # Auto-hide the widget while a fullscreen app/game/video is in front.
    "hide_when_fullscreen": False,

    # Start automatically when Windows boots (toggle from the menu too).
    "autostart": False,

    # Window see-through level, 1.0 = solid, 0.0 = invisible. Try 0.85.
    "opacity": 0.95,

    # ---- Text style ----
    # "System" = follow the actual Windows UI font (what most apps use).
    # Or set any installed font name, e.g. "Segoe UI", "Consolas".
    "font_family": "System",
    "font_bold": True,            # bold numbers -> easier to read on the taskbar
    "font_italic": False,
    # Explicit font point size. null = use the size preset below instead.
    "font_size_override": None,
    # Spaces between the arrow (↓/↑) and the number. Raise/lower to taste.
    "icon_gap": 1,
    # Overall widget size -> tunes font size + padding so the box height can
    # match your taskbar. Options: "small", "medium", "large", "xl".
    "size": "medium",

    # ---- Custom (per-item) colors, like the GitHub TrafficMonitor ----
    # When true, the colors below are used instead of the theme's defaults.
    # (In "transparent" theme the background stays see-through; only the text
    #  colors below are used.)
    "use_custom_colors": False,
    "color_bg": "#1f1f1f",        # widget background
    "color_down": "#4ec9b0",      # download (down arrow) text
    "color_up": "#e8a33d",        # upload (up arrow) text
    "color_total": "#9aa0a6",     # session-total text

    # Show an icon in the system tray / hidden-icons area (needs pystray+Pillow).
    "show_tray_icon": True,

    # Show total data used since the app opened (this session).
    "show_session_total": False,

    # Internal flag -> becomes true once the welcome/credits popup has shown.
    # (Reset deletes config.json, so a fresh install shows the popup again.)
    "intro_shown": False,

    # Where "Snap to corner" puts the widget. The menu can change this.
    #   "top-left", "top-right", "bottom-left", "bottom-right"
    "snap_corner": "bottom-right",
    # Gap (pixels) from the screen edge / taskbar when snapping.
    "snap_margin": 8,
    # For "Snap left of system tray": how many pixels to sit left of the
    # bottom-right corner. Raise it to clear the clock + wifi icons. You can
    # also fine-tune this live with "Tray: nudge left/right" in the menu.
    "tray_offset": 170,

    # Saved widget position. null = let the app pick a default corner first run.
    "position": {"x": None, "y": None},
}

# Size presets -> font size + padding. Pick one from the "Size" menu so the box
# height can match different taskbar heights.
SIZE_PRESETS = {
    "small":  {"font_size": 8,  "padx": 5,  "pady": 1},
    "medium": {"font_size": 10, "padx": 7,  "pady": 2},
    "large":  {"font_size": 12, "padx": 9,  "pady": 3},
    "xl":     {"font_size": 15, "padx": 11, "pady": 4},
}

# Fonts offered in the Options dialog (you can still type any installed font).
# "System" follows the real Windows UI font (see system_font_family()).
COMMON_FONTS = ["System", "Segoe UI", "Tahoma", "Arial", "Calibri", "Verdana",
                "Consolas", "Cascadia Mono", "Courier New", "Times New Roman"]


# =============================================================================
#  Small helpers
# =============================================================================
def app_dir():
    """Folder where config.json lives: next to the .exe (frozen) or this .py."""
    if getattr(sys, "frozen", False):          # True when packaged by PyInstaller
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


CONFIG_PATH = os.path.join(app_dir(), "config.json")


def load_config():
    """Read config.json if present and merge it over the defaults."""
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))  # deep copy of defaults
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            saved = json.load(f)
        for k, v in saved.items():
            if k == "position" and isinstance(v, dict):
                cfg["position"].update(v)
            else:
                cfg[k] = v
    except (FileNotFoundError, ValueError):
        pass  # no/garbled config -> just use defaults
    return cfg


def save_config(cfg):
    """Write current settings so they persist across reboots."""
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except OSError:
        pass  # if we can't write (e.g. read-only folder), just carry on


def windows_is_dark():
    """Return True if Windows is in dark mode. Defaults to dark if unknown."""
    if winreg is None:
        return True
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return value == 0  # 0 = dark apps, 1 = light apps
    except OSError:
        return True


def system_font_family():
    """Return the actual Windows UI font name (what most apps use), so the
    widget matches the system font like the original TrafficMonitor does.
    Falls back to 'Segoe UI' if it can't be read (or off Windows)."""
    if ctypes is not None and hasattr(ctypes, "windll") and wintypes is not None:
        try:
            class LOGFONT(ctypes.Structure):
                _fields_ = [
                    ("lfHeight", wintypes.LONG), ("lfWidth", wintypes.LONG),
                    ("lfEscapement", wintypes.LONG),
                    ("lfOrientation", wintypes.LONG),
                    ("lfWeight", wintypes.LONG), ("lfItalic", wintypes.BYTE),
                    ("lfUnderline", wintypes.BYTE),
                    ("lfStrikeOut", wintypes.BYTE),
                    ("lfCharSet", wintypes.BYTE),
                    ("lfOutPrecision", wintypes.BYTE),
                    ("lfClipPrecision", wintypes.BYTE),
                    ("lfQuality", wintypes.BYTE),
                    ("lfPitchAndFamily", wintypes.BYTE),
                    ("lfFaceName", ctypes.c_wchar * 32),
                ]

            class NONCLIENTMETRICS(ctypes.Structure):
                _fields_ = [
                    ("cbSize", wintypes.UINT),
                    ("iBorderWidth", ctypes.c_int),
                    ("iScrollWidth", ctypes.c_int),
                    ("iScrollHeight", ctypes.c_int),
                    ("iCaptionWidth", ctypes.c_int),
                    ("iCaptionHeight", ctypes.c_int),
                    ("lfCaptionFont", LOGFONT),
                    ("iSmCaptionWidth", ctypes.c_int),
                    ("iSmCaptionHeight", ctypes.c_int),
                    ("lfSmCaptionFont", LOGFONT),
                    ("iMenuWidth", ctypes.c_int),
                    ("iMenuHeight", ctypes.c_int),
                    ("lfMenuFont", LOGFONT),
                    ("lfStatusFont", LOGFONT),
                    ("lfMessageFont", LOGFONT),
                ]
            ncm = NONCLIENTMETRICS()
            ncm.cbSize = ctypes.sizeof(NONCLIENTMETRICS)
            SPI_GETNONCLIENTMETRICS = 0x0029
            ok = ctypes.windll.user32.SystemParametersInfoW(
                SPI_GETNONCLIENTMETRICS, ncm.cbSize, ctypes.byref(ncm), 0)
            if ok and ncm.lfMessageFont.lfFaceName:
                return ncm.lfMessageFont.lfFaceName
        except Exception:
            pass
    return "Segoe UI"


def set_autostart(enable):
    """Add/remove this app from the Windows 'run at login' list."""
    if winreg is None:
        return
    run_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_key, 0,
                             winreg.KEY_SET_VALUE)
        if enable:
            if getattr(sys, "frozen", False):
                command = f'"{sys.executable}"'              # the built .exe
            else:
                # Use pythonw.exe (no console window) to run the script.
                pyw = sys.executable.replace("python.exe", "pythonw.exe")
                command = f'"{pyw}" "{os.path.abspath(__file__)}"'
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except OSError:
                pass
        winreg.CloseKey(key)
    except OSError:
        pass


def foreground_is_fullscreen():
    """True if the foreground window covers the whole screen (a fullscreen
    app/game/video). Used by 'hide when fullscreen'. Windows-only; safely
    returns False everywhere else."""
    if ctypes is None or not hasattr(ctypes, "windll") or wintypes is None:
        return False
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return False
        # Ignore the desktop and the shell/taskbar themselves.
        buf = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, buf, 256)
        if buf.value in ("Progman", "WorkerW", "Shell_TrayWnd"):
            return False
        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        sw = user32.GetSystemMetrics(0)  # SM_CXSCREEN
        sh = user32.GetSystemMetrics(1)  # SM_CYSCREEN
        return (rect.left <= 0 and rect.top <= 0
                and rect.right >= sw and rect.bottom >= sh)
    except Exception:
        return False


def format_speed(bytes_per_sec, units):
    """Turn bytes/second into a short human string per the chosen units.
    No leading-space padding -> the number sits right next to the arrow
    (the gap between arrow and number is controlled by the 'icon_gap' setting)."""
    if units == "Mbps":
        return f"{bytes_per_sec * 8 / 1e6:.1f} Mbps"
    if units == "MBps":
        return f"{bytes_per_sec / 1e6:.2f} MB/s"
    if units == "KBps":
        return f"{bytes_per_sec / 1e3:.1f} KB/s"
    if units == "autokb":
        # KB/MB only -- never falls back to B/s
        if bytes_per_sec >= 1e6:
            return f"{bytes_per_sec / 1e6:.1f} MB/s"
        return f"{bytes_per_sec / 1e3:.0f} KB/s"
    # "auto" (can show B/s when idle)
    if bytes_per_sec >= 1e6:
        return f"{bytes_per_sec / 1e6:.1f} MB/s"
    if bytes_per_sec >= 1e3:
        return f"{bytes_per_sec / 1e3:.0f} KB/s"
    return f"{bytes_per_sec:.0f} B/s"


# =============================================================================
#  The app
# =============================================================================
class TrafficMonitor:
    def __init__(self):
        self.cfg = load_config()

        # network counters: remember the last reading + when we took it
        counters = psutil.net_io_counters()
        self._last_recv = counters.bytes_recv
        self._last_sent = counters.bytes_sent
        self._last_time = time.time()
        self._session_recv = 0  # bytes this session (for optional total)
        self._session_sent = 0
        self._settings_win = None
        # Visibility is the combination of two independent reasons to hide:
        self._fs_active = False      # a fullscreen app is in front
        self._user_hidden = False    # user chose "Hide" from the tray
        self._is_shown = True
        self.tray = None
        # Tray callbacks run on another thread -> they drop work on this queue
        # and the tk main loop runs it safely (tkinter isn't thread-safe).
        self._cmd_q = queue.Queue()

        self._build_window()
        self._build_menu()
        self._apply_theme()
        self._place_window()
        self._build_tray()

        # apply autostart setting on launch so it matches the saved config
        set_autostart(self.cfg["autostart"])

        # Show the colorful welcome / credits popup on the very first run.
        if not self.cfg.get("intro_shown"):
            self.cfg["intro_shown"] = True
            save_config(self.cfg)
            self.root.after(400, self._show_about)

        self._pump_queue()  # start draining tray commands
        self._tick()        # start the update loop

    # ---- window -------------------------------------------------------------
    def _build_window(self):
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} {APP_VERSION}")
        self.root.overrideredirect(True)  # borderless (no title bar)
        self.root.attributes("-topmost", self.cfg["always_on_top"])
        try:
            self.root.attributes("-alpha", float(self.cfg["opacity"]))
        except tk.TclError:
            pass

        # One label per line so each item can have its own color (per-item
        # colors, like the GitHub TrafficMonitor).
        self.frame = tk.Frame(self.root, bd=0, highlightthickness=0)
        self.frame.pack()
        self.down_label = tk.Label(self.frame, justify="left", anchor="w")
        self.up_label = tk.Label(self.frame, justify="left", anchor="w")
        self.total_label = tk.Label(self.frame, justify="left", anchor="w")
        self.down_label.pack(fill="x")
        self.up_label.pack(fill="x")
        self._labels = (self.down_label, self.up_label, self.total_label)
        self._apply_size()  # sets font + padding from the chosen size preset

        # Left-drag to move the widget anywhere; right-click for the menu.
        for w in (self.root, self.frame, self.down_label,
                  self.up_label, self.total_label):
            w.bind("<Button-1>", self._drag_start)
            w.bind("<B1-Motion>", self._drag_move)
            w.bind("<ButtonRelease-1>", self._drag_end)
            w.bind("<Button-3>", self._show_menu)  # right-click = menu

        self.root.protocol("WM_DELETE_WINDOW", self._quit)

    def _drag_start(self, event):
        self._grab_x = event.x
        self._grab_y = event.y

    def _drag_move(self, event):
        if self.cfg.get("lock_position"):
            return  # position locked -> ignore drags
        x = self.root.winfo_pointerx() - self._grab_x
        y = self.root.winfo_pointery() - self._grab_y
        self.root.geometry(f"+{x}+{y}")

    def _drag_end(self, _event):
        if self.cfg.get("lock_position"):
            return
        self.cfg["position"] = {"x": self.root.winfo_x(),
                                "y": self.root.winfo_y()}
        save_config(self.cfg)

    def _place_window(self):
        """Put the window at its saved position, or snap to a corner first run."""
        pos = self.cfg["position"]
        if pos.get("x") is not None and pos.get("y") is not None:
            self.root.geometry(f"+{pos['x']}+{pos['y']}")
        else:
            self._snap_to_corner(self.cfg["snap_corner"])

    def _snap_to_corner(self, corner):
        """Move the widget against one screen corner (used by the menu too)."""
        self.cfg["snap_corner"] = corner
        self.root.update_idletasks()  # make sure size is known
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        m = self.cfg["snap_margin"]
        # Leave a little room for the taskbar on bottom snaps.
        taskbar = 48
        x = m if "left" in corner else sw - w - m
        y = m if "top" in corner else sh - h - taskbar - m
        self.root.geometry(f"+{x}+{y}")
        self.cfg["position"] = {"x": x, "y": y}
        save_config(self.cfg)

    def _snap_to_tray(self):
        """Sit just left of the system-tray icons (near the wifi/clock),
        vertically centered in the taskbar so the heights line up."""
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        taskbar = 48  # typical taskbar height; fine-tune with tray_offset
        x = sw - w - self.cfg["tray_offset"]
        y = sh - taskbar + max((taskbar - h) // 2, 0)  # center inside taskbar
        self.root.geometry(f"+{x}+{y}")
        self.cfg["position"] = {"x": x, "y": y}
        save_config(self.cfg)

    def _nudge_tray(self, dx):
        """Shift the tray position left (+) / right (-) to clear icons."""
        self.cfg["tray_offset"] = max(self.cfg["tray_offset"] + dx, 0)
        save_config(self.cfg)
        self._snap_to_tray()

    def _current_font_size(self):
        """The effective font point size: explicit override, else the preset."""
        preset = SIZE_PRESETS.get(self.cfg.get("size", "medium"),
                                  SIZE_PRESETS["medium"])
        return self.cfg.get("font_size_override") or preset["font_size"]

    def _apply_size(self):
        """Apply font (family/size/bold/italic) + padding to all the lines."""
        preset = SIZE_PRESETS.get(self.cfg.get("size", "medium"),
                                  SIZE_PRESETS["medium"])
        size = self._current_font_size()
        styles = []
        if self.cfg.get("font_bold", True):
            styles.append("bold")
        if self.cfg.get("font_italic", False):
            styles.append("italic")
        style = " ".join(styles) if styles else "normal"
        family = self.cfg["font_family"]
        if not family or family == "System":
            family = system_font_family()   # follow the real Windows UI font
        font = (family, size, style)
        for lbl in self._labels:
            lbl.configure(font=font, padx=preset["padx"],
                          pady=max(preset["pady"] - 1, 0))

    def _reset_defaults(self):
        """Restore every setting to DEFAULT_CONFIG (the 'reset' option)."""
        self.cfg = json.loads(json.dumps(DEFAULT_CONFIG))
        save_config(self.cfg)
        self.root.attributes("-topmost", self.cfg["always_on_top"])
        self._apply_size()
        self._apply_theme()
        self._place_window()
        set_autostart(self.cfg["autostart"])

    # ---- About / Credits ----------------------------------------------------
    def _show_about(self):
        """Colorful welcome / credits popup. Shows on first run and from the menu.
        Edit the CREDIT / TITLE / TAGLINE strings below to change the wording."""
        # ---- text you can freely edit ----
        TITLE = "TrafficMonitor"
        TAGLINE = "Real-time network speed meter"
        CREDIT_TOP = "Instructed & created with AI by"
        CREDIT_NAME = "OR_Mahim"
        # ----------------------------------

        win = tk.Toplevel(self.root)
        win.title("About  •  TrafficMonitor")
        win.resizable(False, False)
        win.attributes("-topmost", True)
        w, h = 400, 250
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

        canvas = tk.Canvas(win, width=w, height=h, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        # Smooth vertical gradient (purple -> blue) for a professional look.
        top_rgb, bottom_rgb = (124, 58, 237), (37, 99, 235)
        for i in range(h):
            r = int(top_rgb[0] + (bottom_rgb[0] - top_rgb[0]) * i / h)
            g = int(top_rgb[1] + (bottom_rgb[1] - top_rgb[1]) * i / h)
            b = int(top_rgb[2] + (bottom_rgb[2] - top_rgb[2]) * i / h)
            canvas.create_line(0, i, w, i, fill=f"#{r:02x}{g:02x}{b:02x}")

        canvas.create_text(w // 2, 44, text=TITLE, fill="#ffffff",
                           font=("Segoe UI", 24, "bold"))
        canvas.create_text(w // 2, 74, text=TAGLINE, fill="#dbeafe",
                           font=("Segoe UI", 10))
        canvas.create_text(w // 2, 96, text=f"v{APP_VERSION}", fill="#bfdbfe",
                           font=("Segoe UI", 9))
        canvas.create_text(w // 2, 146, text=CREDIT_TOP, fill="#e9d5ff",
                           font=("Segoe UI", 11))
        canvas.create_text(w // 2, 174, text=CREDIT_NAME, fill="#fde047",
                           font=("Segoe UI", 20, "bold"))

        btn = tk.Button(win, text="Let's go  ✓", command=win.destroy,
                        bg="#111827", fg="#ffffff", activebackground="#1f2937",
                        activeforeground="#ffffff", relief="flat",
                        padx=18, pady=4, cursor="hand2",
                        font=("Segoe UI", 10, "bold"))
        canvas.create_window(w // 2, 220, window=btn)

        win.transient(self.root)
        win.focus_force()

    # ---- Options dialog -----------------------------------------------------
    def _show_settings(self):
        """The 'Options' window: Taskbar window settings (colors + font) and
        General settings (lock / always-on-top / hide-when-fullscreen)."""
        # If it's already open, just bring it to the front.
        if self._settings_win is not None and self._settings_win.winfo_exists():
            self._settings_win.lift()
            self._settings_win.focus_force()
            return

        win = tk.Toplevel(self.root)
        self._settings_win = win
        win.title(f"Options  •  {APP_NAME} {APP_VERSION}")
        win.resizable(False, False)
        win.attributes("-topmost", True)

        # ---- working copies of the settings (written back only on Apply) ----
        use_custom = tk.BooleanVar(value=self.cfg["use_custom_colors"])
        color_vars = {
            "color_bg":    tk.StringVar(value=self.cfg["color_bg"]),
            "color_down":  tk.StringVar(value=self.cfg["color_down"]),
            "color_up":    tk.StringVar(value=self.cfg["color_up"]),
            "color_total": tk.StringVar(value=self.cfg["color_total"]),
        }
        font_family = tk.StringVar(value=self.cfg["font_family"])
        font_size = tk.IntVar(value=self._current_font_size())
        font_bold = tk.BooleanVar(value=self.cfg["font_bold"])
        font_italic = tk.BooleanVar(value=self.cfg.get("font_italic", False))
        icon_gap = tk.IntVar(value=int(self.cfg.get("icon_gap", 1)))
        lock_pos = tk.BooleanVar(value=self.cfg["lock_position"])
        on_top = tk.BooleanVar(value=self.cfg["always_on_top"])
        hide_fs = tk.BooleanVar(value=self.cfg["hide_when_fullscreen"])
        tray_on = tk.BooleanVar(value=self.cfg.get("show_tray_icon", True))

        pad = {"padx": 8, "pady": 4}

        # ===== Taskbar window settings =====
        tb = ttk.LabelFrame(win, text="Taskbar window settings")
        tb.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))

        ttk.Checkbutton(tb, text="Use custom colors (off = follow theme)",
                        variable=use_custom).grid(
            row=0, column=0, columnspan=3, sticky="w", **pad)

        def make_color_row(r, label, key):
            ttk.Label(tb, text=label).grid(row=r, column=0, sticky="w", **pad)
            swatch = tk.Button(tb, width=6, relief="groove",
                               bg=color_vars[key].get())

            def pick():
                _, hexc = colorchooser.askcolor(
                    color_vars[key].get(), parent=win, title=f"{label} color")
                if hexc:
                    color_vars[key].set(hexc)
                    swatch.configure(bg=hexc)
            swatch.configure(command=pick)
            swatch.grid(row=r, column=1, sticky="w", **pad)
            ttk.Label(tb, textvariable=color_vars[key]).grid(
                row=r, column=2, sticky="w", **pad)

        make_color_row(1, "Background", "color_bg")
        make_color_row(2, "Download  ↓", "color_down")
        make_color_row(3, "Upload  ↑", "color_up")
        make_color_row(4, "Session total  ∑", "color_total")

        # Font row
        ttk.Label(tb, text="Font").grid(row=5, column=0, sticky="w", **pad)
        fcombo = ttk.Combobox(tb, textvariable=font_family, values=COMMON_FONTS,
                              width=18)
        fcombo.grid(row=5, column=1, columnspan=2, sticky="w", **pad)

        ttk.Label(tb, text="Size").grid(row=6, column=0, sticky="w", **pad)
        ttk.Spinbox(tb, from_=6, to=48, width=5,
                    textvariable=font_size).grid(row=6, column=1, sticky="w",
                                                 **pad)
        styles = ttk.Frame(tb)
        styles.grid(row=6, column=2, sticky="w", **pad)
        ttk.Checkbutton(styles, text="Bold", variable=font_bold).pack(side="left")
        ttk.Checkbutton(styles, text="Italic",
                        variable=font_italic).pack(side="left", padx=(8, 0))

        # Gap between the arrow (↓/↑) and the number.
        ttk.Label(tb, text="Gap (arrow ↔ number)").grid(
            row=7, column=0, sticky="w", **pad)
        ttk.Spinbox(tb, from_=0, to=8, width=5,
                    textvariable=icon_gap).grid(row=7, column=1, sticky="w",
                                                **pad)

        # ===== General settings =====
        gen = ttk.LabelFrame(win, text="General settings")
        gen.grid(row=1, column=0, sticky="ew", padx=10, pady=6)
        ttk.Checkbutton(gen, text="Lock window position",
                        variable=lock_pos).grid(row=0, column=0, sticky="w", **pad)
        ttk.Checkbutton(gen, text="Always on top",
                        variable=on_top).grid(row=1, column=0, sticky="w", **pad)
        ttk.Checkbutton(gen, text="Hide main window when a program is fullscreen",
                        variable=hide_fs).grid(row=2, column=0, sticky="w", **pad)
        ttk.Checkbutton(gen, text="Show system-tray icon (restart to apply)",
                        variable=tray_on).grid(row=3, column=0, sticky="w", **pad)

        # ===== buttons =====
        def apply():
            self.cfg["use_custom_colors"] = bool(use_custom.get())
            for k, var in color_vars.items():
                self.cfg[k] = var.get()
            self.cfg["font_family"] = font_family.get().strip() or "System"
            try:
                self.cfg["font_size_override"] = int(font_size.get())
            except (tk.TclError, ValueError):
                pass
            self.cfg["font_bold"] = bool(font_bold.get())
            self.cfg["font_italic"] = bool(font_italic.get())
            try:
                self.cfg["icon_gap"] = max(int(icon_gap.get()), 0)
            except (tk.TclError, ValueError):
                pass
            self.cfg["lock_position"] = bool(lock_pos.get())
            self.cfg["always_on_top"] = bool(on_top.get())
            self.root.attributes("-topmost", self.cfg["always_on_top"])
            self.cfg["hide_when_fullscreen"] = bool(hide_fs.get())
            self.cfg["show_tray_icon"] = bool(tray_on.get())
            save_config(self.cfg)
            self._apply_size()
            self._apply_theme()

        def ok():
            apply()
            close()

        def close():
            self._settings_win = None
            win.destroy()

        bar = ttk.Frame(win)
        bar.grid(row=2, column=0, sticky="e", padx=10, pady=(6, 10))
        ttk.Button(bar, text="Apply", command=apply).pack(side="left", padx=4)
        ttk.Button(bar, text="OK", command=ok).pack(side="left", padx=4)
        ttk.Button(bar, text="Cancel", command=close).pack(side="left", padx=4)

        ttk.Label(win, text=f"{APP_NAME} v{APP_VERSION}",
                  foreground="#888").grid(row=3, column=0, sticky="w",
                                          padx=12, pady=(0, 8))

        win.protocol("WM_DELETE_WINDOW", close)
        # Center on screen.
        win.update_idletasks()
        w, h = win.winfo_width(), win.winfo_height()
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        win.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")
        win.focus_force()

    # ---- right-click menu ---------------------------------------------------
    def _build_menu(self):
        # Menu state variables -> these drive the radio dots / check ticks so
        # the menu always shows what's currently selected.
        self._var_refresh = tk.DoubleVar(value=float(self.cfg["refresh_seconds"]))
        self._var_units = tk.StringVar(value=self.cfg["units"])
        self._var_theme = tk.StringVar(value=self.cfg["theme"])
        self._var_size = tk.StringVar(value=self.cfg["size"])
        self._var_on_top = tk.BooleanVar(value=self.cfg["always_on_top"])
        self._var_lock = tk.BooleanVar(value=self.cfg["lock_position"])
        self._var_fullscreen = tk.BooleanVar(value=self.cfg["hide_when_fullscreen"])
        self._var_session = tk.BooleanVar(value=self.cfg["show_session_total"])
        self._var_autostart = tk.BooleanVar(value=self.cfg["autostart"])

        self.menu = tk.Menu(self.root, tearoff=0)

        # Version header (disabled, just informational).
        self.menu.add_command(label=f"{APP_NAME}  v{APP_VERSION}",
                              state="disabled")
        self.menu.add_separator()
        self.menu.add_command(label="Settings…", command=self._show_settings)
        self.menu.add_separator()

        # Refresh rate (radio -> shows the selected one)
        rate_menu = tk.Menu(self.menu, tearoff=0)
        for secs in (0.5, 1.0, 2.0, 5.0):
            rate_menu.add_radiobutton(
                label=f"{secs:g} s", value=secs, variable=self._var_refresh,
                command=self._menu_set_refresh)
        self.menu.add_cascade(label="Refresh rate", menu=rate_menu)

        # Units (radio)
        units_menu = tk.Menu(self.menu, tearoff=0)
        for u, lbl in (("autokb", "Auto (KB/MB, no B/s)"),
                       ("auto", "Auto (B/KB/MB)"),
                       ("KBps", "KB/s"),
                       ("MBps", "MB/s"),
                       ("Mbps", "Mbps (like ISP)")):
            units_menu.add_radiobutton(label=lbl, value=u,
                                       variable=self._var_units,
                                       command=self._menu_set_units)
        self.menu.add_cascade(label="Units", menu=units_menu)

        # Theme (radio)
        theme_menu = tk.Menu(self.menu, tearoff=0)
        for t in ("auto", "dark", "light", "transparent"):
            theme_menu.add_radiobutton(label=t.capitalize(), value=t,
                                       variable=self._var_theme,
                                       command=self._menu_set_theme)
        self.menu.add_cascade(label="Theme", menu=theme_menu)

        # Size (radio)
        size_menu = tk.Menu(self.menu, tearoff=0)
        for s in ("small", "medium", "large", "xl"):
            size_menu.add_radiobutton(label=s.capitalize(), value=s,
                                      variable=self._var_size,
                                      command=self._menu_set_size)
        self.menu.add_cascade(label="Size", menu=size_menu)

        # Snap (corners + system tray)
        snap_menu = tk.Menu(self.menu, tearoff=0)
        for c in ("top-left", "top-right", "bottom-left", "bottom-right"):
            snap_menu.add_command(
                label=c.replace("-", " ").title(),
                command=lambda x=c: self._snap_to_corner(x))
        snap_menu.add_separator()
        snap_menu.add_command(label="Left of system tray",
                              command=self._snap_to_tray)
        snap_menu.add_command(label="Tray: nudge left  ◄",
                              command=lambda: self._nudge_tray(20))
        snap_menu.add_command(label="Tray: nudge right ►",
                              command=lambda: self._nudge_tray(-20))
        self.menu.add_cascade(label="Snap", menu=snap_menu)

        # Toggles (check -> shows a ✓ tick when on)
        self.menu.add_separator()
        self.menu.add_checkbutton(label="Always on top",
                                  variable=self._var_on_top,
                                  command=self._menu_on_top)
        self.menu.add_checkbutton(label="Lock window position",
                                  variable=self._var_lock,
                                  command=self._menu_lock)
        self.menu.add_checkbutton(
            label="Hide when fullscreen", variable=self._var_fullscreen,
            command=self._menu_fullscreen)
        self.menu.add_checkbutton(label="Session total",
                                  variable=self._var_session,
                                  command=self._menu_session)
        self.menu.add_checkbutton(label="Start with Windows",
                                  variable=self._var_autostart,
                                  command=self._menu_autostart)

        self.menu.add_separator()
        self.menu.add_command(label="About / Credits", command=self._show_about)
        self.menu.add_command(label="Reset all settings",
                              command=self._reset_defaults)
        self.menu.add_command(label="Quit", command=self._quit)

    def _sync_menu_vars(self):
        """Make the menu's ticks/dots match the current saved settings."""
        self._var_refresh.set(float(self.cfg["refresh_seconds"]))
        self._var_units.set(self.cfg["units"])
        self._var_theme.set(self.cfg["theme"])
        self._var_size.set(self.cfg["size"])
        self._var_on_top.set(self.cfg["always_on_top"])
        self._var_lock.set(self.cfg["lock_position"])
        self._var_fullscreen.set(self.cfg["hide_when_fullscreen"])
        self._var_session.set(self.cfg["show_session_total"])
        self._var_autostart.set(self.cfg["autostart"])

    def _show_menu(self, event):
        self._sync_menu_vars()
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    # ---- menu command handlers (read the var, apply, save) ------------------
    def _menu_set_refresh(self):
        self._set("refresh_seconds", float(self._var_refresh.get()))

    def _menu_set_units(self):
        self._set("units", self._var_units.get())

    def _menu_set_theme(self):
        self._set("theme", self._var_theme.get())
        self._apply_theme()

    def _menu_set_size(self):
        self._set("size", self._var_size.get())
        self._apply_size()

    def _menu_on_top(self):
        self.cfg["always_on_top"] = bool(self._var_on_top.get())
        self.root.attributes("-topmost", self.cfg["always_on_top"])
        save_config(self.cfg)

    def _menu_lock(self):
        self._set("lock_position", bool(self._var_lock.get()))

    def _menu_fullscreen(self):
        self._set("hide_when_fullscreen", bool(self._var_fullscreen.get()))

    def _menu_session(self):
        self._set("show_session_total", bool(self._var_session.get()))

    def _menu_autostart(self):
        self.cfg["autostart"] = bool(self._var_autostart.get())
        set_autostart(self.cfg["autostart"])
        save_config(self.cfg)

    # ---- settings helpers ---------------------------------------------------
    def _set(self, key, value):
        self.cfg[key] = value
        save_config(self.cfg)

    # ---- theme --------------------------------------------------------------
    def _apply_theme(self):
        choice = self.cfg["theme"]
        custom = self.cfg.get("use_custom_colors", False)

        # Always clear any previous color-key transparency first.
        try:
            self.root.attributes("-transparentcolor", "")
        except tk.TclError:
            pass

        if choice == "transparent":
            # Background becomes fully see-through (Windows only). Only the text
            # shows -- so to drag / right-click, click ON the numbers.
            key = "#010101"  # near-black key color that won't appear in text
            if custom:
                down = self.cfg["color_down"]
                up = self.cfg["color_up"]
                total = self.cfg["color_total"]
            else:
                # Vivid mid-tone colors that stay readable on BOTH light and
                # dark taskbars -- this fixes text blending into the background.
                down, up, total = "#19c37d", "#ff8c42", "#ffd24a"
            self.root.configure(bg=key)
            self.frame.configure(bg=key)
            self._paint_labels(key, down, up, total)
            try:
                self.root.attributes("-transparentcolor", key)
            except tk.TclError:
                pass  # not on Windows -> falls back to showing the key color
            return

        if custom:
            bg = self.cfg["color_bg"]
            down = self.cfg["color_down"]
            up = self.cfg["color_up"]
            total = self.cfg["color_total"]
        else:
            dark = windows_is_dark() if choice == "auto" else (choice == "dark")
            if dark:
                bg, fg, total = "#1f1f1f", "#e6e6e6", "#9aa0a6"
            else:
                bg, fg, total = "#f3f3f3", "#1a1a1a", "#6b6b6b"
            down = up = fg
        self.root.configure(bg=bg)
        self.frame.configure(bg=bg)
        self._paint_labels(bg, down, up, total)

    def _paint_labels(self, bg, down, up, total):
        self.down_label.configure(bg=bg, fg=down)
        self.up_label.configure(bg=bg, fg=up)
        self.total_label.configure(bg=bg, fg=total)

    # ---- visibility / keep-on-top / fullscreen -----------------------------
    def _apply_visibility(self):
        """Show the widget only when nothing wants it hidden (a fullscreen app,
        or the user picked 'Hide' from the tray). Tray icon stays either way."""
        should_show = not self._fs_active and not self._user_hidden
        if should_show and not self._is_shown:
            self.root.deiconify()
            self._is_shown = True
            self._keep_on_top()
        elif not should_show and self._is_shown:
            self.root.withdraw()
            self._is_shown = False

    def _keep_on_top(self):
        """Re-assert topmost every tick so the widget is never buried behind a
        window you just opened (the bug where it vanished on the taskbar)."""
        if self.cfg["always_on_top"] and self._is_shown:
            try:
                self.root.attributes("-topmost", True)
                self.root.lift()
            except tk.TclError:
                pass

    def _handle_fullscreen(self):
        """Track whether a fullscreen app is in front, then update visibility."""
        want = bool(self.cfg.get("hide_when_fullscreen")) and \
            foreground_is_fullscreen()
        if want != self._fs_active:
            self._fs_active = want
            self._apply_visibility()

    # ---- system tray icon ---------------------------------------------------
    def _build_tray(self):
        """Add the notification-area (system tray) icon, if pystray+Pillow are
        available and the setting is on. Its menu works even while the widget
        is hidden behind a fullscreen app."""
        if pystray is None or make_image is None:
            return
        if not self.cfg.get("show_tray_icon", True):
            return
        image = make_image(64)
        if image is None:
            return
        menu = pystray.Menu(
            pystray.MenuItem("Show / Hide", self._tray_toggle, default=True),
            pystray.MenuItem("Settings…",
                             lambda *a: self._post(self._show_settings)),
            pystray.MenuItem("About",
                             lambda *a: self._post(self._show_about)),
            pystray.MenuItem(
                "Start with Windows", self._tray_autostart,
                checked=lambda item: self.cfg["autostart"]),
            pystray.MenuItem("Quit", lambda *a: self._post(self._quit)),
        )
        try:
            self.tray = pystray.Icon(APP_NAME, image,
                                     f"{APP_NAME} {APP_VERSION}", menu)
            self.tray.run_detached()   # runs the tray on its own thread
        except Exception:
            self.tray = None           # any backend hiccup -> just no tray

    def _post(self, fn):
        """Hand a callback from the tray thread back to the tk main thread."""
        self._cmd_q.put(fn)

    def _pump_queue(self):
        """Run any callbacks queued by the tray thread, then reschedule."""
        try:
            while True:
                self._cmd_q.get_nowait()()
        except queue.Empty:
            pass
        except Exception:
            pass
        self.root.after(100, self._pump_queue)

    def _tray_toggle(self, *_a):
        def do():
            self._user_hidden = not self._user_hidden
            self._apply_visibility()
        self._post(do)

    def _tray_autostart(self, *_a):
        def do():
            self.cfg["autostart"] = not self.cfg["autostart"]
            set_autostart(self.cfg["autostart"])
            save_config(self.cfg)
        self._post(do)

    # ---- the live update loop ----------------------------------------------
    def _read_speeds(self):
        """Return (download_bytes_per_sec, upload_bytes_per_sec) since last call."""
        now = time.time()
        counters = psutil.net_io_counters()
        elapsed = max(now - self._last_time, 1e-6)
        down = (counters.bytes_recv - self._last_recv) / elapsed
        up = (counters.bytes_sent - self._last_sent) / elapsed
        # track session totals
        self._session_recv += max(counters.bytes_recv - self._last_recv, 0)
        self._session_sent += max(counters.bytes_sent - self._last_sent, 0)
        self._last_recv = counters.bytes_recv
        self._last_sent = counters.bytes_sent
        self._last_time = now
        return max(down, 0), max(up, 0)

    def _refresh_text(self, down, up):
        units = self.cfg["units"]
        gap = " " * max(int(self.cfg.get("icon_gap", 1)), 0)
        self.down_label.configure(text=f"↓{gap}{format_speed(down, units)}")
        self.up_label.configure(text=f"↑{gap}{format_speed(up, units)}")
        if self.cfg["show_session_total"]:
            tot_d = self._session_recv / 1e6
            tot_u = self._session_sent / 1e6
            self.total_label.configure(text=f"∑{gap}{tot_d:.1f}/{tot_u:.1f} MB")
            if not self.total_label.winfo_ismapped():
                self.total_label.pack(fill="x")
        elif self.total_label.winfo_ismapped():
            self.total_label.pack_forget()

    def _tick(self):
        down, up = self._read_speeds()
        self._refresh_text(down, up)
        # re-check Windows theme occasionally so "auto" follows live changes
        if self.cfg["theme"] == "auto":
            self._apply_theme()
        self._keep_on_top()
        self._handle_fullscreen()
        delay = max(int(self.cfg["refresh_seconds"] * 1000), 200)
        self.root.after(delay, self._tick)

    # ---- shutdown -----------------------------------------------------------
    def _quit(self):
        save_config(self.cfg)
        if self.tray is not None:
            try:
                self.tray.stop()
            except Exception:
                pass
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    if "--version" in sys.argv or "-v" in sys.argv:
        print(f"{APP_NAME} {APP_VERSION}")
        sys.exit(0)
    TrafficMonitor().run()
