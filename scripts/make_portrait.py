"""One-off: turn assets/avatar.png into assets/portrait.txt (ASCII) for the hero card.

Pencil-sketch pass (colour dodge of the blurred negative) so the outlines and
features carry the drawing, then a density ramp. Needs Pillow, so it runs
locally, not in the daily workflow. Re-run only when the avatar changes.
"""
from pathlib import Path
from PIL import Image, ImageChops, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent.parent
COLS, CW, CH = 120, 2.4, 4.4
RAMP = "   .:-=+*cs#%@@"

a = Image.open(ROOT / "assets" / "avatar.png").convert("RGBA")
alpha = a.getchannel("A")
g = a.convert("L")
blur = ImageOps.invert(g).filter(ImageFilter.GaussianBlur(10))
gp, bp = g.load(), blur.load()
sketch = Image.new("L", g.size)
sp = sketch.load()
for y in range(g.size[1]):
    for x in range(g.size[0]):
        b = bp[x, y]
        sp[x, y] = 255 if b >= 255 else min(255, gp[x, y] * 255 // (255 - b))
sketch = sketch.point(lambda v: int(255 * (v / 255) ** 3))
tone = g.point(lambda v: 255 - int((255 - v) * 0.45))
g = Image.composite(ImageChops.multiply(sketch, tone), Image.new("L", g.size, 255), alpha)
rows = round(COLS * (g.size[1] / g.size[0]) * (CW / CH))
g = g.resize((COLS, rows), Image.LANCZOS)
lines = ["".join(RAMP[min(len(RAMP) - 1, int((255 - g.getpixel((x, y))) / 256 * len(RAMP)))] for x in range(COLS)).rstrip()
         for y in range(rows)]
(ROOT / "assets" / "portrait.txt").write_text("\n".join(lines) + "\n")
print(COLS, rows)
