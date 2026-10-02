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
    uid = f"ic{round(x)}_{round(y)}"
    return (f'<g transform="rotate({rot} {n(x + s / 2)} {n(y + s / 2)})">'
            f'<rect x="{n(x - 5)}" y="{n(y + 3)}" width="{n(s + 10)}" height="{n(s + 10)}" rx="{n(rx + 5)}" fill="#000" opacity=".22" filter="url(#soft)"/>'
            f'<rect x="{n(x - 5)}" y="{n(y - 5)}" width="{n(s + 10)}" height="{n(s + 10)}" rx="{n(rx + 5)}" fill="#fff"/>'
            f'<clipPath id="{uid}"><rect x="{n(x)}" y="{n(y)}" width="{n(s)}" height="{n(s)}" rx="{n(rx)}"/></clipPath>'
            f'<image href="data:image/png;base64,{icon}" x="{n(x)}" y="{n(y)}" width="{n(s)}" height="{n(s)}" clip-path="url(#{uid})"/></g>')


GITHUB_MARK = ("M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49"
               "-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52"
               ".28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18"
               " 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87"
               " 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z")
USERNAME = "Siddhart111"


def github_tag(right: float, bottom: float, size: float = 16) -> str:
    """A small white square-cornered tag - the GitHub mark and my username - anchored by its bottom-right corner."""
    from fontTools.ttLib import TTFont
    mono = TTFont(CACHE / FONTS["GeistMono"][0])
    advance = mono["hmtx"]["zero"][0] / mono["head"].unitsPerEm
    track = .04
    text_w = len(USERNAME) * advance * size + (len(USERNAME) - 1) * track * size
    h, pad, mark = size * 2.4, size * .95, size * 1.25
    w = pad + mark + size * .6 + text_w + pad
    x, y = right - w, bottom - h
    k = mark / 16
    return (f'<rect x="{n(x)}" y="{n(y + 3)}" width="{n(w)}" height="{n(h)}" fill="#000" opacity=".2" filter="url(#soft)"/>'
            f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" fill="#fff"/>'
            f'<path d="{GITHUB_MARK}" fill="{C["ink"]}" transform="translate({n(x + pad)} {n(y + (h - mark) / 2)}) scale({k:.4g})"/>'
            f'<text x="{n(x + pad + mark + size * .6)}" y="{n(y + h / 2)}" dominant-baseline="central" font-family="GeistMono" '
            f'font-weight="500" font-size="{n(size)}" letter-spacing="{n(track * size)}" fill="{C["ink"]}">{USERNAME}</text>')


COUNT = "2,000+"                     # the owner's number for the banner (2 Oct)
COUNT_LABEL = "JOINED FUTURE"


def _gauss(color: str, peak: float = 1.0) -> str:
    return "".join(f'<stop offset="{x / 10:g}" stop-color="{color}" '
                   f'stop-opacity="{peak * math.exp(-4.5 * (x / 10) ** 2) if x < 10 else 0:.3f}"/>' for x in range(11))


# Aria exactly as the app draws her (frontend/src/ui/AriaPearl.tsx), as one still frame:
# colour, size, swing, height, period, phase, opacity of each blob of colour
ARIA_BLOBS = [("#EC86A5", .52, .15, -.06, 1.0, 0.0, .85), ("#FFBBA0", .48, .16, .10, 1.3, .35, .85),
              ("#FFD8BE", .44, .14, -.14, 1.6, .7, .8), ("#FFE9F0", .40, .12, .04, 1.15, .5, .85),
              ("#E0668C", .36, .16, .12, 1.9, .15, .6)]
ARIA_BODY = [(0, "#FCE1EA", .96), (.3, "#F3B2C7", .95), (.42, "#EDA5BD", .93), (.478, "#EBA0B8", .904),
             (.536, "#EBA0B8", .833), (.594, "#EBA0B8", .729), (.652, "#EBA0B8", .603), (.71, "#EBA0B8", .465),
             (.768, "#EBA0B8", .327), (.826, "#EBA0B8", .201), (.884, "#EBA0B8", .097), (.942, "#EBA0B8", .026),
             (1, "#EBA0B8", 0)]
ARIA_HALO = [(.3, 0), (.44, .14), (.58, .17), (.7, .12), (.82, .055), (.92, .015), (1, 0)]
EYE = "#2B1D22"


def aria(cx: float, cy: float, size: float) -> str:
    """Her face as in the app: a soft rose pearl that melts into the page, colour drifting
    inside, a glossy spot, the grain, two espresso eyes with a highlight, a line of a smile."""
    D = size * .92
    x0, y0 = cx - D / 2, cy - D / 2               # the pearl's box
    top = cy - size / 2                           # the face box (eyes at .41, smile at .55)
    grain = base64.b64encode((ASSETS / "src" / "aria-grain.png").read_bytes()).decode()
    defs = ['<radialGradient id="aHalo">' + "".join(f'<stop offset="{o}" stop-color="#EDA5BD" stop-opacity="{a}"/>'
                                                   for o, a in ARIA_HALO) + '</radialGradient>',
            '<radialGradient id="aBody" cx="50%" cy="50%" r="50%" fx="45%" fy="42%">'
            + "".join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a}"/>' for o, c, a in ARIA_BODY)
            + '</radialGradient>',
            '<radialGradient id="aSheen"><stop offset="0" stop-color="#fff" stop-opacity=".75"/>'
            '<stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>']
    out = [f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{n(size * .7)}" fill="url(#aHalo)"/>',
           f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{n(D / 2)}" fill="url(#aBody)"/>']
    for i, (c, s, R, lat, _, ph, o) in enumerate(ARIA_BLOBS):
        z = (1 + math.cos(2 * math.pi * ph)) / 2          # nearer the front: bigger and brighter
        bs = s * D * (.72 + .4 * z)
        defs.append(f'<radialGradient id="aB{i}">{_gauss(c, o)}</radialGradient>')
        out.append(f'<circle cx="{n(cx + math.sin(2 * math.pi * ph) * R * D)}" cy="{n(cy + lat * D)}" r="{n(bs / 2)}" '
                   f'fill="url(#aB{i})" opacity="{.22 + .78 * z:.3f}"/>')
    out.append(f'<image href="data:image/png;base64,{grain}" x="{n(x0)}" y="{n(y0)}" width="{n(D)}" height="{n(D)}"/>')
    out.append(f'<circle cx="{n(x0 + D * .34)}" cy="{n(y0 + D * .26)}" r="{n(D * .2)}" fill="url(#aSheen)"/>')
    eyeW, eyeH, gap = size * .078, size * .112, size * .104
    for side in (-1, 1):
        ex, ey = cx + side * gap - eyeW / 2, top + size * .41 - eyeH / 2
        out.append(f'<rect x="{n(ex)}" y="{n(ey)}" width="{n(eyeW)}" height="{n(eyeH)}" rx="{n(eyeW / 2)}" fill="{EYE}"/>')
        out.append(f'<circle cx="{n(ex + eyeW * .34)}" cy="{n(ey + eyeH * .34)}" r="{n(eyeW * .17)}" fill="#fff"/>')
    my, half, sag = top + size * .55, size * .078, size * .042
    out.append(f'<path d="M{n(cx - half)} {n(my)}Q{n(cx)} {n(my + 2 * sag)} {n(cx + half)} {n(my)}" fill="none" '
               f'stroke="{EYE}" stroke-width="{n(size * .017)}" stroke-linecap="round"/>')
    return f'<defs>{"".join(defs)}</defs>' + "".join(out)


def meet_aria(cx: float, cy: float) -> str:
    """On the yellow circle (the owner's picks, 2 Oct): MEET ARIA, Aria as in the app on a
    little round of the app's own blush grid paper, and the count in white on a red tag."""
    dx, dy, dr = cx, cy - 40, 74                  # the round of blush paper she sits on
    cell = 12
    grid = "".join(f'<path d="M{dx - dr + k * cell} {dy - dr}V{dy + dr}M{dx - dr} {dy - dr + k * cell}H{dx + dr}"/>'
                   for k in range(int(2 * dr / cell) + 1))
    tag_w, tag_h, ty = 196, 70, cy + 70
    return (f'<text x="{n(cx)}" y="{n(cy - 126)}" font-family="GeistMono" font-weight="600" font-size="13" '
            f'letter-spacing="3.5" text-anchor="middle" fill="#111111">MEET ARIA</text>'
            f'<clipPath id="paper"><circle cx="{n(dx)}" cy="{n(dy)}" r="{dr}"/></clipPath>'
            f'<circle cx="{n(dx)}" cy="{n(dy)}" r="{dr}" fill="#FBF4F1"/>'
            f'<g clip-path="url(#paper)"><g stroke="#8B6A5C" stroke-opacity=".16" stroke-width=".7">{grid}</g>'
            + aria(dx, dy + 4, 158) + '</g>'
            + f'<g transform="rotate(-4 {n(cx)} {n(ty + tag_h / 2)})">'
              f'<rect x="{n(cx - tag_w / 2)}" y="{n(ty + 4)}" width="{tag_w}" height="{tag_h}" fill="#000" opacity=".18" filter="url(#soft)"/>'
              f'<rect x="{n(cx - tag_w / 2)}" y="{n(ty)}" width="{tag_w}" height="{tag_h}" fill="#FF2A00"/>'
              f'<text x="{n(cx)}" y="{n(ty + 41)}" font-family="Bricolage" font-weight="800" font-size="42" fill="#fff" '
              f'text-anchor="middle" letter-spacing="-1.5" style="font-variation-settings:&quot;opsz&quot; 96">{COUNT}</text>'
              f'<text x="{n(cx)}" y="{n(ty + 59)}" font-family="GeistMono" font-weight="600" font-size="12" fill="#fff" '
              f'text-anchor="middle" letter-spacing="2.6">{COUNT_LABEL}</text></g>')

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
        sticker(150, 300, 96, -12),
        sticker(470, 14, 84, 12),
        sparkle(735, 598, 20, C["white"]),
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
        sticker(160, 420, 120, -12),
        sticker(566, 290, 104, -8),
        sparkle(990, 330, 30, C["white"]),
        sparkle(120, 1060, 20, C["white"]),
    ])


def linkedin(center: str | None = None) -> tuple[int, int, str]:
    """LinkedIn's banner, 1584 x 396 (4:1). LinkedIn lays the profile photo over the bottom
    left (about x < 380, y > 230 here) and phones trim the sides a little, so the name and
    the yellow circle sit in the middle and the right; only the letters circle runs under the photo.
    No photo of me here (the owner, 2 Oct): LinkedIn shows it beside the banner anyway."""
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
        f'<circle cx="868" cy="318" r="92" fill="{C["red"]}"/>',          # red now, behind the yellow
        polka(1060, 418, 96, "pk", 30, 7.5),
        f'<circle cx="712" cy="200" r="168" fill="{C["yellow"]}"/>',     # where my photo was (the owner, 2 Oct)
        meet_aria(712, 200) if center is None else center,            # what sits on the yellow circle
        sticker(1196, 206, 92, 9),
        sticker(120, 110, 76, -12),
        sticker(500, 14, 70, 12),
        sparkle(604, 372, 16, C["white"]),
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
