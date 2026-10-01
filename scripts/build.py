"""Builds the collage at the top of this profile:  python scripts/build.py  ->  assets/hero.png + hero-phone.png

A flat-colour collage: big overlapping circles, the letters of my name scattered round one,
my photo in another, a pink circle of contour lines, polka dots, giant cropped initials and the Future app
icon as a sticker. Drawn as SVG, then rendered to PNG with headless Chrome - one wide version
for desktop, one tall version for phones.

    pip install fonttools pillow       # and Google Chrome
"""
from __future__ import annotations

import base64
import io
import math
import random
import subprocess
import urllib.request
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

NAME = "Siddharth Nishad"
CAPTION = "DESIGNER & ENGINEER — FOUNDER OF FUTURE"
AVATAR = "https://avatars.githubusercontent.com/u/140869328?v=4&s=460"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
C = dict(violet="#6B2BFF", blue="#1023D6", mint="#47F2B8", red="#FF3D00", maroon="#2B0600",
         green="#00A443", yellow="#FFC700", pink="#FF9CC6", line="#FF1F45", white="#FFFFFF",
         orange="#FF6A1F", lime="#C9FF4D", ink="#111111")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ASSETS = ROOT / "assets"
CACHE = HERE / ".fonts"
GF = "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/"
FONTS = {  # OFL
    "Bricolage": ("BricolageGrotesque.ttf", GF + "bricolagegrotesque/BricolageGrotesque%5Bopsz%2Cwdth%2Cwght%5D.ttf"),
    "GeistMono": ("GeistMono.ttf", GF + "geistmono/GeistMono%5Bwght%5D.ttf"),
}


def n(v: float) -> str:
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def fetch(url: str, path: Path) -> bytes:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, path)
    return path.read_bytes()


def font_css() -> str:
    out = []
    for family, (file, url) in FONTS.items():
        data = base64.b64encode(fetch(url, CACHE / file)).decode()
        out.append(f"@font-face{{font-family:{family};src:url(data:font/ttf;base64,{data});font-weight:100 900;}}")
    return "".join(out)


# ------------------------------------------------------------------------------ pieces
FACE = (20, 40, 400, 420)      # the part of the avatar that goes in the circle: face, hair, collar


def photo(cx: float, cy: float, r: float, uid: str, scale: int) -> str:
    """My photo as it is, cut to a circle - no colour on it. Sized for the final render
    and sharpened a touch, since the avatar is only 460 px."""
    src = Image.open(io.BytesIO(fetch(AVATAR, CACHE / "avatar.jpg"))).convert("RGB")
    side = round(2 * r * scale)
    img = src.crop(FACE).resize((side, side), Image.LANCZOS)
    img = img.filter(ImageFilter.UnsharpMask(radius=1.4, percent=55, threshold=2))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=93, subsampling=0)
    data = base64.b64encode(buf.getvalue()).decode()
    return (f'<clipPath id="{uid}"><circle cx="{n(cx)}" cy="{n(cy)}" r="{n(r)}"/></clipPath>'
            f'<image href="data:image/jpeg;base64,{data}" x="{n(cx - r)}" y="{n(cy - r)}" width="{n(2 * r)}" '
            f'height="{n(2 * r)}" clip-path="url(#{uid})"/>')


def letters(cx: float, cy: float, radius: float, size: float, seed: int = 7) -> str:
    """The letters of my name, scattered round a circle, each at its own angle."""
    rnd = random.Random(seed)
    chars = [c for c in NAME if c != " "]
    out = []
    for i, ch in enumerate(chars):
        a = math.radians(-200 + i * 360 / len(chars) + rnd.uniform(-6, 6))
        rr = radius + rnd.uniform(-14, 14)
        x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
        rot = math.degrees(a) + 90 + rnd.uniform(-35, 35) + (180 if rnd.random() < .22 else 0)
        out.append(f'<text x="{n(x)}" y="{n(y)}" transform="rotate({n(rot)} {n(x)} {n(y)})">{ch}</text>')
    return (f'<g fill="{C["mint"]}" font-family="Bricolage" font-weight="700" font-size="{n(size)}" '
            f'text-anchor="middle" dominant-baseline="central" style="font-variation-settings:\'opsz\' 96">{"".join(out)}</g>')


def contours(cx: float, cy: float, rings: int, gap: float, seed: int = 3) -> str:
    rnd = random.Random(seed)
    paths = []
    for k in range(rings):
        base = 24 + k * gap
        ph1, ph2 = rnd.uniform(0, 6.3), rnd.uniform(0, 6.3)
        pts = []
        for t in range(0, 361, 4):
            a = math.radians(t)
            rr = base + 9 * math.sin(3 * a + ph1) + 6 * math.sin(5 * a + ph2) + k * 1.5 * math.sin(2 * a)
            pts.append(f"{n(cx + rr * math.cos(a))} {n(cy + rr * math.sin(a))}")
        paths.append("M" + "L".join(pts) + "Z")
    return f'<path d="{"".join(paths)}" fill="none" stroke="{C["line"]}" stroke-width="3"/>'


def polka(cx: float, cy: float, r: float, uid: str, gap: float = 34, dot: float = 8.5) -> str:
    dots = "".join(f'<circle cx="{n(x)}" cy="{n(y)}" r="{dot}"/>'
                   for x in [cx - r + gap / 2 + i * gap for i in range(int(2 * r / gap) + 1)]
                   for y in [cy - r + gap / 2 + j * gap + (gap / 2 if int((x - cx + r) / gap) % 2 else 0)
                             for j in range(int(2 * r / gap) + 1)])
    return (f'<clipPath id="{uid}"><circle cx="{n(cx)}" cy="{n(cy)}" r="{n(r)}"/></clipPath>'
            f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{n(r)}" fill="#FF2424"/>'
            f'<g clip-path="url(#{uid})" fill="#fff">{dots}</g>')


def sparkle(x: float, y: float, s: float, color: str) -> str:
    return (f'<path d="M{n(x)} {n(y - s)}Q{n(x)} {n(y)} {n(x + s)} {n(y)}Q{n(x)} {n(y)} {n(x)} {n(y + s)}'
            f'Q{n(x)} {n(y)} {n(x - s)} {n(y)}Q{n(x)} {n(y)} {n(x)} {n(y - s)}Z" fill="{color}"/>')


def sticker(x: float, y: float, s: float, rot: float) -> str:
    """The Future app icon, stuck on at an angle."""
    icon = base64.b64encode((ASSETS / "src" / "future-icon.png").read_bytes()).decode()
    rx = s * .225
    return (f'<g transform="rotate({rot} {n(x + s / 2)} {n(y + s / 2)})">'
            f'<rect x="{n(x - 5)}" y="{n(y + 3)}" width="{n(s + 10)}" height="{n(s + 10)}" rx="{n(rx + 5)}" fill="#000" opacity=".22" filter="url(#soft)"/>'
            f'<rect x="{n(x - 5)}" y="{n(y - 5)}" width="{n(s + 10)}" height="{n(s + 10)}" rx="{n(rx + 5)}" fill="#fff"/>'
            f'<clipPath id="ic"><rect x="{n(x)}" y="{n(y)}" width="{n(s)}" height="{n(s)}" rx="{n(rx)}"/></clipPath>'
            f'<image href="data:image/png;base64,{icon}" x="{n(x)}" y="{n(y)}" width="{n(s)}" height="{n(s)}" clip-path="url(#ic)"/></g>')


def giant(ch: str, x: float, y: float, size: float, color: str) -> str:
    return (f'<text x="{n(x)}" y="{n(y)}" font-family="Bricolage" font-weight="800" font-size="{n(size)}" fill="{color}" '
            f'style="font-variation-settings:\'opsz\' 96,\'wdth\' 75">{ch}</text>')


# ------------------------------------------------------------------------------ layouts
def desktop() -> tuple[int, int, str]:
    W, H = 1280, 640
    P = dict(bx=250, by=400, br=286,          # blue circle
             px=652, py=312, pr=244,          # portrait
             kx=1092, ky=410, kr=252)         # pink circle
    return W, H, "".join([
        f'<rect width="{W}" height="{H}" fill="{C["violet"]}"/>',
        f'<rect x="470" width="420" height="{H}" fill="{C["green"]}"/>',
        f'<rect x="890" width="390" height="{H}" fill="{C["orange"]}"/>',
        giant("S", -40, 560, 760, C["lime"]),
        giant("N", 930, 760, 820, C["yellow"]),
        f'<circle cx="{P["bx"]}" cy="{P["by"]}" r="{P["br"]}" fill="{C["blue"]}"/>',
        letters(P["bx"], P["by"], P["br"] - 62, 62),
        f'<clipPath id="kc"><circle cx="{P["kx"]}" cy="{P["ky"]}" r="{P["kr"]}"/></clipPath>',
        f'<circle cx="{P["kx"]}" cy="{P["ky"]}" r="{P["kr"]}" fill="{C["pink"]}"/>',
        f'<g clip-path="url(#kc)">{contours(P["kx"] + 40, P["ky"] + 30, 13, 24)}</g>',
        f'<rect x="760" width="{W - 760}" height="120" fill="{C["white"]}"/>',
        f'<text x="786" y="74" font-family="Bricolage" font-weight="700" font-size="62" fill="#FF2A00" '
        f'letter-spacing="-1.5" style="font-variation-settings:\'opsz\' 96">{NAME}</text>',
        f'<text x="788" y="104" font-family="GeistMono" font-weight="500" font-size="13" fill="{C["ink"]}" '
        f'letter-spacing="1.6">{CAPTION}</text>',
        f'<circle cx="812" cy="468" r="112" fill="{C["yellow"]}"/>',
        polka(905, 640, 112, "pk"),
        photo(P["px"], P["py"], P["pr"], "pc", 2),
        sticker(1112, 186, 104, 9),
        sparkle(540, 70, 22, C["white"]),
        sparkle(1015, 590, 16, C["white"]),
        sparkle(395, 610, 13, C["yellow"]),
    ])


def phone() -> tuple[int, int, str]:
    W, H = 1080, 1350
    return W, H, "".join([
        f'<rect width="{W}" height="{H}" fill="{C["violet"]}"/>',
        f'<rect x="540" y="230" width="540" height="{H}" fill="{C["green"]}"/>',
        f'<rect y="980" width="{W}" height="370" fill="{C["orange"]}"/>',
        giant("S", -50, 900, 900, C["lime"]),
        giant("N", 700, 1480, 900, C["yellow"]),
        f'<rect width="{W}" height="230" fill="{C["white"]}"/>',
        f'<text x="48" y="128" font-family="Bricolage" font-weight="700" font-size="112" fill="#FF2A00" '
        f'letter-spacing="-3" style="font-variation-settings:\'opsz\' 96">{NAME}</text>',
        f'<text x="52" y="188" font-family="GeistMono" font-weight="500" font-size="23.5" fill="{C["ink"]}" '
        f'letter-spacing="2.4">{CAPTION}</text>',
        f'<circle cx="300" cy="560" r="330" fill="{C["blue"]}"/>',
        letters(300, 560, 258, 74),
        f'<clipPath id="kc"><circle cx="890" cy="1150" r="330"/></clipPath>',
        f'<circle cx="890" cy="1150" r="330" fill="{C["pink"]}"/>',
        f'<g clip-path="url(#kc)">{contours(930, 1180, 16, 26)}</g>',
        f'<circle cx="905" cy="900" r="140" fill="{C["yellow"]}"/>',
        polka(200, 1300, 170, "pk", 40, 10),
        photo(680, 790, 330, "pc", 1),
        sticker(880, 1110, 150, -8),
        sparkle(990, 330, 30, C["white"]),
        sparkle(120, 1060, 20, C["white"]),
    ])


def linkedin() -> tuple[int, int, str]:
    """LinkedIn's banner, 1584 x 396 (4:1). LinkedIn lays the profile photo over the bottom
    left (about x < 380, y > 230 here) and phones trim the sides a little, so the name and
    the photo sit in the middle and the right; only the letters circle runs under the photo."""
    W, H = 1584, 396
    return W, H, "".join([
        f'<rect width="{W}" height="{H}" fill="{C["violet"]}"/>',
        f'<rect x="520" width="520" height="{H}" fill="{C["green"]}"/>',
        f'<rect x="1040" width="{W - 1040}" height="{H}" fill="{C["orange"]}"/>',
        giant("S", -30, 470, 600, C["lime"]),
        giant("N", 1300, 560, 600, C["yellow"]),
        f'<circle cx="235" cy="205" r="232" fill="{C["blue"]}"/>',
        letters(235, 205, 176, 52),
        f'<clipPath id="kc"><circle cx="1395" cy="372" r="206"/></clipPath>',
        f'<circle cx="1395" cy="372" r="206" fill="{C["pink"]}"/>',
        f'<g clip-path="url(#kc)">{contours(1425, 392, 11, 22)}</g>',
        f'<rect x="938" width="{W - 938}" height="148" fill="{C["white"]}"/>',
        f'<text x="968" y="86" font-family="Bricolage" font-weight="700" font-size="64" fill="#FF2A00" '
        f'letter-spacing="-1.6" style="font-variation-settings:\'opsz\' 96">{NAME}</text>',
        f'<text x="971" y="121" font-family="GeistMono" font-weight="500" font-size="14" fill="{C["ink"]}" '
        f'letter-spacing="1.7">{CAPTION}</text>',
        f'<circle cx="868" cy="318" r="92" fill="{C["yellow"]}"/>',
        polka(1060, 418, 96, "pk", 30, 7.5),
        photo(712, 200, 168, "pc", 2),
        sticker(1196, 206, 92, 9),
        sparkle(560, 52, 20, C["white"]),
        sparkle(1550, 196, 15, C["white"]),
        sparkle(950, 362, 12, C["white"]),
    ])


def render(layout, out: Path, scale: int) -> None:
    W, H, body = layout()
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
           f'<defs><style>{font_css()}</style><filter id="soft"><feGaussianBlur stdDeviation="6"/></filter></defs>'
           f'{body}</svg>')
    page = HERE / ".render.html"
    page.write_text(f'<!doctype html><html><head><meta charset="utf-8"></head><body style="margin:0">{svg}</body></html>', encoding="utf-8")
    shot = HERE / ".render.png"
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--force-device-scale-factor={scale}",
                    f"--window-size={W},{H}", "--virtual-time-budget=3000", f"--screenshot={shot}", page.as_uri()],
                   check=True, timeout=180, capture_output=True)
    img = Image.open(shot).convert("RGB")
    img.save(out, optimize=True)
    page.unlink()
    shot.unlink()
    print(out.name, img.size, round(out.stat().st_size / 1024), "KB")


def main() -> None:
    render(desktop, ASSETS / "hero.png", 2)
    render(phone, ASSETS / "hero-phone.png", 1)


if __name__ == "__main__":
    main()
