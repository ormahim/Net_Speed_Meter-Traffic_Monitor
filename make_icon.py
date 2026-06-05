"""
Make the app icon.

  * Run directly to (re)create "icon.ico" (used for the .exe + the tray):
        python make_icon.py
  * monitor.py also imports make_image() from here to draw the tray icon.

Only needs Pillow:  pip install pillow
The drawing is a dark rounded square with a teal download arrow and an
orange upload arrow -- matching the widget's default colors.
"""

try:
    from PIL import Image, ImageDraw
except Exception:                # Pillow not installed -> tray/icon just skipped
    Image = None
    ImageDraw = None

TEAL = (78, 201, 176, 255)       # download  (matches color_down default)
ORANGE = (232, 163, 61, 255)     # upload    (matches color_up default)
BG = (31, 31, 31, 255)           # dark rounded square


def make_image(size=64):
    """Return a PIL RGBA Image of the icon, or None if Pillow is missing."""
    if Image is None:
        return None
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = max(size // 16, 1)
    d.rounded_rectangle([pad, pad, size - pad, size - pad],
                        radius=size // 5, fill=BG)

    bar = max(int(size * 0.08), 2)           # arrow stem thickness
    head = int(size * 0.16)                   # arrowhead half-width

    # Download arrow (teal), left side, pointing down.
    lx = int(size * 0.36)
    d.line([(lx, int(size * 0.28)), (lx, int(size * 0.60))],
           fill=TEAL, width=bar)
    d.polygon([(lx - head, int(size * 0.55)), (lx + head, int(size * 0.55)),
               (lx, int(size * 0.74))], fill=TEAL)

    # Upload arrow (orange), right side, pointing up.
    rx = int(size * 0.64)
    d.line([(rx, int(size * 0.40)), (rx, int(size * 0.72))],
           fill=ORANGE, width=bar)
    d.polygon([(rx - head, int(size * 0.45)), (rx + head, int(size * 0.45)),
               (rx, int(size * 0.26))], fill=ORANGE)
    return img


if __name__ == "__main__":
    if Image is None:
        raise SystemExit("Pillow not installed. Run:  pip install pillow")
    sizes = [16, 24, 32, 48, 64, 128, 256]
    base = make_image(256)
    base.save("icon.ico", sizes=[(s, s) for s in sizes])
    print("Wrote icon.ico")
