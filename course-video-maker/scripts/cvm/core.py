"""Drawing core: antialiased shapes, icons, text helpers and easing (1920x1080, 30 fps)."""
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1920, 1080, 30
import os as _os
FD = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))), "assets", "fonts") + "/"
MONO = FD + "DejaVuSansMono.ttf"
MONOB = FD + "DejaVuSansMono.ttf"
HAND = FD + "kalam-latin-700-normal.woff"
HAND_R = FD + "kalam-latin-400-normal.woff"

BG = (11, 12, 24)
AMBER = (255, 184, 28)
AMBER_SOFT = (255, 236, 190)
WHITE = (255, 255, 255)
INK = (22, 24, 36)
MUTED = (150, 156, 178)
GREEN = (52, 199, 120)
RED = (240, 72, 72)
BLUE = (37, 99, 235)
CARD = (27, 29, 48)
CARD2 = (38, 41, 66)
LINE = (62, 66, 96)
UI_BG = (255, 255, 255)
UI_SIDE = (246, 247, 250)
UI_LINE = (222, 225, 232)
UI_TEXT = (28, 30, 40)
UI_MUTED = (110, 116, 130)

_F = {}
def font(name, size):
    key = (name, int(size))
    f = _F.get(key)
    if f is None:
        path = name if name.startswith("/") else FD + name
        f = _F[key] = ImageFont.truetype(path, int(size))
    return f
def fb(s): return font("Inter-Bold.otf", s)
def fx(s): return font("InterDisplay-ExtraBold.otf", s)
def fk(s): return font("InterDisplay-Black.otf", s)
def fs(s): return font("Inter-SemiBold.otf", s)
def fr(s): return font("Inter-Regular.otf", s)
def fm(s): return font(MONO, s)
def fmb(s): return font(MONOB, s)

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def easeio(x): x = clamp(x); return x * x * (3 - 2 * x)
def back(x):
    x = clamp(x); c = 1.70158; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def lerp(a, b, k): return a + (b - a) * k
def mix(c1, c2, k): return tuple(int(lerp(a, b, clamp(k))) for a, b in zip(c1, c2))
def A(col, a): return tuple(col[:3]) + (int(clamp(a, 0, 255)),)

class Clock:
    """Scene clock: t seconds into a scene of dur seconds; times in args are fractions of dur."""
    def __init__(self, t, dur): self.t, self.dur = t, dur
    @property
    def f(self): return self.t / self.dur if self.dur else 1.0
    def sec(self, frac): return frac * self.dur
    def ap(self, frac, d=0.45):
        """0..1 entrance progress for something that appears at fraction frac."""
        if frac is None: return 1.0
        return clamp((self.t - frac * self.dur) / d)
    def since(self, frac): return self.t - frac * self.dur

# ------------------------------------------------------------------ antialiased rounded rectangles
_MASK = {}
def _rmask(w, h, r, ow=0):
    key = (w, h, r, ow)
    m = _MASK.get(key)
    if m is None:
        if len(_MASK) > 4000: _MASK.clear()
        s = 3
        big = Image.new("L", (w * s, h * s), 0); bd = ImageDraw.Draw(big)
        bd.rounded_rectangle([0, 0, w * s - 1, h * s - 1], r * s, fill=255)
        if ow and 2 * ow < min(w, h):
            bd.rounded_rectangle([ow * s, ow * s, w * s - 1 - ow * s, h * s - 1 - ow * s], max(0, r - ow) * s, fill=0)
        m = _MASK[key] = big.resize((w, h), Image.LANCZOS)
    return m
_LUT = {}
def _scale_mask(m, a):
    if a >= 0.999: return m
    k = int(a * 64)
    lut = _LUT.get(k)
    if lut is None: lut = _LUT[k] = [int(v * k / 64) for v in range(256)]
    return m.point(lut)
def _paste_color(img, col, x0, y0, m):
    w, h = m.size
    cx0, cy0, cx1, cy1 = max(0, x0), max(0, y0), min(img.width, x0 + w), min(img.height, y0 + h)
    if cx1 <= cx0 or cy1 <= cy0: return
    if (cx0, cy0, cx1, cy1) != (x0, y0, x0 + w, y0 + h):
        m = m.crop((cx0 - x0, cy0 - y0, cx1 - x0, cy1 - y0))
    img.paste(tuple(col[:3]), (cx0, cy0, cx1, cy1), m)

def rr(img, box, r, fill=None, outline=None, width=2, alpha=1.0):
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    w, h = x1 - x0, y1 - y0
    if w <= 1 or h <= 1 or alpha <= 0.01: return
    r = int(max(0, min(r, w // 2, h // 2)))
    if fill is not None:
        a = alpha * (fill[3] / 255 if len(fill) == 4 else 1)
        if a > 0.01: _paste_color(img, fill, x0, y0, _scale_mask(_rmask(w, h, r), a))
    if outline is not None and width > 0:
        a = alpha * (outline[3] / 255 if len(outline) == 4 else 1)
        if a > 0.01: _paste_color(img, outline, x0, y0, _scale_mask(_rmask(w, h, r, int(width)), a))

def circle(img, cx, cy, r, fill=None, outline=None, width=2, alpha=1.0):
    rr(img, (cx - r, cy - r, cx + r, cy + r), r, fill, outline, width, alpha)

def glow(img, box, r=14, col=AMBER, alpha=1.0, pulse=0.0):
    """Amber highlight box around a UI element (the 'button name in a highlighted box' rule)."""
    x0, y0, x1, y1 = box
    g = 8 + 3 * pulse
    rr(img, (x0 - g - 6, y0 - g - 6, x1 + g + 6, y1 + g + 6), r + g + 6, fill=A(col, 40), alpha=alpha)
    rr(img, (x0 - g, y0 - g, x1 + g, y1 + g), r + g, outline=col, width=4, alpha=alpha)

# ------------------------------------------------------------------ text
def tw(f, s): return f.getlength(s)
def text(d, xy, s, f, fill, anchor="la"):
    if len(fill) == 4 and fill[3] <= 2: return
    d.text(xy, s, font=f, fill=fill, anchor=anchor)
def wrap(s, f, maxw):
    words, lines, cur = s.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if tw(f, t) <= maxw or not cur: cur = t
        else: lines.append(cur); cur = w_
    if cur: lines.append(cur)
    return lines
def fit(s, name, size, maxw, floor=14):
    f = font(name, size)
    while tw(f, s) > maxw and size > floor:
        size -= 2; f = font(name, size)
    return f

def paste_rgba(img, im, x, y, alpha=1.0):
    x, y = int(round(x)), int(round(y))
    if alpha <= 0.01: return
    if alpha < 0.999:
        im = im.copy(); a = im.getchannel("A").point([int(v * alpha) for v in range(256)]); im.putalpha(a)
    img.paste(im, (x, y), im)

def blur_region(img, box, radius=6):
    x0, y0, x1, y1 = [int(v) for v in box]
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(img.width, x1), min(img.height, y1)
    if x1 - x0 < 2 or y1 - y0 < 2: return
    img.paste(img.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(radius)), (x0, y0))

# ------------------------------------------------------------------ icons (drawn at 4x, cached)
_ICON = {}
def icon(name, size, col=WHITE):
    key = (name, int(size), tuple(col))
    im = _ICON.get(key)
    if im is not None: return im
    s = 4; S = int(size) * s
    big = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(big)
    c = tuple(col[:3]) + (255,)
    u = S / 100.0
    def L(*pts, w=7): d.line([(x * u, y * u) for x, y in pts], fill=c, width=int(w * u), joint="curve")
    def R(x0, y0, x1, y1, r=6, fill=True, w=7):
        if fill: d.rounded_rectangle([x0 * u, y0 * u, x1 * u, y1 * u], r * u, fill=c)
        else: d.rounded_rectangle([x0 * u, y0 * u, x1 * u, y1 * u], r * u, outline=c, width=int(w * u))
    def E(x0, y0, x1, y1, fill=True, w=7):
        if fill: d.ellipse([x0 * u, y0 * u, x1 * u, y1 * u], fill=c)
        else: d.ellipse([x0 * u, y0 * u, x1 * u, y1 * u], outline=c, width=int(w * u))
    def PG(*pts): d.polygon([(x * u, y * u) for x, y in pts], fill=c)
    def CUT(x0, y0, x1, y1, r=6, ell=False):
        if ell: d.ellipse([x0 * u, y0 * u, x1 * u, y1 * u], fill=(0, 0, 0, 0))
        else: d.rounded_rectangle([x0 * u, y0 * u, x1 * u, y1 * u], r * u, fill=(0, 0, 0, 0))
    n = name
    if n == "laptop": R(18, 22, 82, 66, 5, False, 7); R(6, 70, 94, 78, 3)
    elif n == "phone": R(30, 8, 70, 92, 9, False, 7); E(46, 80, 54, 88)
    elif n == "camera": R(8, 28, 70, 76, 8); PG((72, 44), (94, 32), (94, 72), (72, 60))
    elif n == "mic": R(36, 8, 64, 58, 14); L((24, 46), (24, 50)); d.arc([24 * u, 26 * u, 76 * u, 72 * u], 0, 180, fill=c, width=int(7 * u)); L((50, 72), (50, 88)); L((36, 90), (64, 90))
    elif n == "folder": PG((8, 24), (40, 24), (48, 32), (92, 32), (92, 82), (8, 82))
    elif n == "file": PG((22, 8), (62, 8), (80, 26), (80, 92), (22, 92)); CUT(32, 44, 70, 50, 2); CUT(32, 58, 70, 64, 2); CUT(32, 72, 58, 78, 2)
    elif n == "code": L((36, 26), (14, 50), (36, 74), w=9); L((64, 26), (86, 50), (64, 74), w=9); L((56, 18), (44, 82), w=7)
    elif n == "triangle": PG((50, 14), (90, 84), (10, 84))
    elif n == "bolt": PG((58, 6), (18, 58), (48, 58), (40, 94), (82, 40), (52, 40))
    elif n == "spark": PG((50, 6), (60, 40), (94, 50), (60, 60), (50, 94), (40, 60), (6, 50), (40, 40))
    elif n == "vidiq":
        f = ImageFont.truetype(FD + "InterDisplay-Black.otf", int(40 * u)); d.text((50 * u, 52 * u), "vIQ", font=f, fill=c, anchor="mm")
    elif n == "claude":
        for k in range(12):
            a = k * math.pi / 6; r1 = 44 if k % 2 == 0 else 34
            L((50 + 8 * math.cos(a), 50 + 8 * math.sin(a)), (50 + r1 * math.cos(a), 50 + r1 * math.sin(a)), w=9)
    elif n == "instagram": R(12, 12, 88, 88, 24, False, 8); E(32, 32, 68, 68, False, 8); E(68, 22, 78, 32)
    elif n == "telegram": PG((8, 46), (90, 12), (74, 88), (48, 70), (36, 86), (34, 64), (78, 26), (28, 58))
    elif n == "youtube": R(6, 20, 94, 80, 20); d.polygon([(42 * u, 36 * u), (66 * u, 50 * u), (42 * u, 64 * u)], fill=(0, 0, 0, 0))
    elif n == "meta":
        pts = [(50 + 40 * math.cos(k / 60 * 2 * math.pi) / (1 + math.sin(k / 60 * 2 * math.pi) ** 2),
                50 + 40 * math.sin(k / 60 * 2 * math.pi) * math.cos(k / 60 * 2 * math.pi) / (1 + math.sin(k / 60 * 2 * math.pi) ** 2) * 1.5) for k in range(61)]
        L(*pts, w=10)
    elif n == "gauge": d.arc([10 * u, 18 * u, 90 * u, 98 * u], 180, 360, fill=c, width=int(10 * u)); L((50, 58), (72, 34), w=8); E(42, 50, 58, 66)
    elif n == "server": R(14, 12, 86, 42, 6); R(14, 54, 86, 84, 6); CUT(24, 24, 34, 30, 2); CUT(24, 66, 34, 72, 2)
    elif n == "person": E(34, 8, 66, 40); PG((16, 92), (20, 62), (36, 50), (64, 50), (80, 62), (84, 92))
    elif n == "group": E(14, 20, 38, 44); E(62, 20, 86, 44); E(36, 10, 64, 38); PG((4, 88), (8, 60), (26, 52), (74, 52), (92, 60), (96, 88))
    elif n == "clock": E(8, 8, 92, 92, False, 8); L((50, 22), (50, 50), (70, 62), w=8)
    elif n == "house": PG((50, 8), (94, 46), (82, 46), (82, 92), (18, 92), (18, 46), (6, 46)); CUT(40, 60, 60, 92, 3)
    elif n == "grid":
        R(8, 14, 92, 86, 8)
        for gx in (36, 64): CUT(gx - 2, 18, gx + 2, 82, 1)
        for gy in (34, 52, 70): CUT(12, gy - 2, 88, gy + 2, 1)
    elif n == "bell": PG((50, 10), (70, 22), (76, 60), (88, 74), (12, 74), (24, 60), (30, 22)); E(42, 76, 58, 92)
    elif n == "key": E(6, 30, 46, 70, False, 9); L((44, 50), (92, 50), w=10); L((80, 50), (80, 66), w=9); L((66, 50), (66, 62), w=9)
    elif n == "lock": R(18, 44, 82, 92, 8); d.arc([30 * u, 14 * u, 70 * u, 60 * u], 180, 360, fill=c, width=int(9 * u)); L((30, 36), (30, 46), w=9); L((70, 36), (70, 46), w=9); CUT(46, 60, 54, 76, 2)
    elif n == "warning": PG((50, 8), (96, 90), (4, 90)); CUT(46, 36, 54, 66, 2); CUT(45, 72, 55, 82, 5, True)
    elif n == "check": L((14, 52), (40, 76), (86, 26), w=12)
    elif n == "cross": L((20, 20), (80, 80), w=12); L((80, 20), (20, 80), w=12)
    elif n == "robot": R(18, 28, 82, 82, 12); L((50, 10), (50, 28), w=6); E(44, 4, 56, 16); CUT(30, 44, 44, 58, 7, True); CUT(56, 44, 70, 58, 7, True); CUT(36, 66, 64, 72, 2)
    elif n == "chat": R(8, 12, 92, 70, 14); PG((24, 66), (24, 90), (46, 68))
    elif n == "plug": L((38, 8), (38, 30), w=8); L((62, 8), (62, 30), w=8); R(24, 28, 76, 58, 8); L((50, 58), (50, 92), w=9)
    elif n == "heart": E(10, 16, 52, 58); E(48, 16, 90, 58); PG((12, 44), (88, 44), (50, 90))
    elif n == "play": PG((26, 12), (86, 50), (26, 88))
    elif n == "pause": R(24, 14, 42, 86, 4); R(58, 14, 76, 86, 4)
    elif n == "chart": R(10, 56, 28, 90, 3); R(40, 36, 58, 90, 3); R(70, 14, 88, 90, 3)
    elif n == "calendar": R(8, 16, 92, 92, 8, False, 7); R(8, 16, 92, 36, 6); L((28, 6), (28, 24), w=8); L((72, 6), (72, 24), w=8)
    elif n == "cloud": E(10, 40, 50, 80); E(30, 18, 76, 64); E(52, 40, 92, 80); R(30, 56, 72, 80, 4)
    elif n == "wave":
        for k, hh in enumerate((20, 40, 64, 40, 80, 50, 30, 56, 24)):
            x = 10 + k * 10; L((x, 50 - hh / 2), (x, 50 + hh / 2), w=6)
    elif n == "link": d.arc([8 * u, 30 * u, 54 * u, 70 * u], 90, 270, fill=c, width=int(8 * u)); d.arc([46 * u, 30 * u, 92 * u, 70 * u], 270, 450, fill=c, width=int(8 * u)); L((32, 50), (68, 50), w=8)
    elif n == "renew": d.arc([12 * u, 12 * u, 88 * u, 88 * u], 20, 320, fill=c, width=int(9 * u)); PG((86, 36), (90, 8), (64, 24))
    elif n == "upload": L((50, 70), (50, 14), w=9); L((28, 36), (50, 14), (72, 36), w=9); L((14, 70), (14, 88), (86, 88), (86, 70), w=8)
    elif n == "gear":
        for k in range(8):
            a = k * math.pi / 4; L((50 + 30 * math.cos(a), 50 + 30 * math.sin(a)), (50 + 44 * math.cos(a), 50 + 44 * math.sin(a)), w=14)
        E(18, 18, 82, 82); CUT(36, 36, 64, 64, 14, True)
    elif n == "chai": R(16, 30, 70, 90, 10); d.arc([58 * u, 42 * u, 90 * u, 74 * u], 270, 450, fill=c, width=int(7 * u)); L((34, 8), (30, 22), w=5); L((50, 8), (46, 22), w=5)
    elif n == "star": PG(*[(50 + (44 if k % 2 == 0 else 18) * math.cos(-math.pi / 2 + k * math.pi / 5), 52 + (44 if k % 2 == 0 else 18) * math.sin(-math.pi / 2 + k * math.pi / 5)) for k in range(10)])
    elif n == "bulb": E(24, 8, 76, 60); R(36, 58, 64, 74, 3); R(38, 78, 62, 86, 3); CUT(44, 30, 56, 56, 2)
    elif n == "rupee": L((26, 16), (76, 16), w=8); L((26, 34), (76, 34), w=8); d.arc([10 * u, 4 * u, 62 * u, 62 * u], 270, 450, fill=c, width=int(8 * u)); L((36, 62), (26, 62), (70, 94), w=9)
    elif n == "book": PG((8, 18), (46, 24), (46, 90), (8, 84)); PG((54, 24), (92, 18), (92, 84), (54, 90))
    elif n == "target": E(6, 6, 94, 94, False, 8); E(24, 24, 76, 76, False, 8); E(42, 42, 58, 58)
    elif n == "rocket": PG((50, 4), (70, 30), (70, 70), (30, 70), (30, 30)); PG((30, 50), (14, 74), (30, 70)); PG((70, 50), (86, 74), (70, 70)); PG((40, 74), (60, 74), (50, 96)); CUT(42, 32, 58, 48, 8, True)
    elif n == "trophy": d.arc([8 * u, 12 * u, 36 * u, 48 * u], 90, 270, fill=c, width=int(7 * u)); d.arc([64 * u, 12 * u, 92 * u, 48 * u], 270, 450, fill=c, width=int(7 * u)); PG((24, 10), (76, 10), (70, 50), (56, 60), (44, 60), (30, 50)); R(44, 58, 56, 76, 2); R(28, 78, 72, 90, 4)
    elif n == "search": E(8, 8, 66, 66, False, 9); L((58, 58), (90, 90), w=12)
    elif n == "video": R(6, 22, 70, 78, 10); PG((74, 40), (94, 28), (94, 72), (74, 60))
    elif n == "pen": PG((70, 8), (92, 30), (34, 88), (10, 92), (12, 68)); CUT(64, 22, 70, 28, 1)
    elif n == "question": d.arc([22 * u, 6 * u, 78 * u, 58 * u], 200, 430, fill=c, width=int(10 * u)); L((50, 56), (50, 70), w=10); E(44, 80, 56, 92)
    elif n == "money": R(4, 24, 96, 76, 8); CUT(38, 36, 62, 64, 12, True)
    elif n == "teacher": E(56, 8, 84, 36); PG((46, 92), (50, 50), (90, 50), (94, 92)); R(6, 14, 46, 50, 4, False, 6); L((40, 50), (62, 60), w=6)
    elif n == "excel": R(8, 8, 92, 92, 10); CUT(26, 26, 74, 74, 4); L((34, 34), (66, 66), w=9); L((66, 34), (34, 66), w=9)
    elif n == "whatsapp": E(8, 8, 92, 92, False, 8); PG((8, 92), (18, 66), (34, 82))
    else: E(20, 20, 80, 80)
    im = big.resize((int(size), int(size)), Image.LANCZOS)
    _ICON[key] = im
    return im

def logo_tile(img, app, cx, cy, size, alpha=1.0, apps=None):
    """App logo: a coloured rounded tile with a white glyph."""
    col, glyph = apps[app]
    x0, y0 = cx - size / 2, cy - size / 2
    if app == "Instagram":
        key = ("__ig", int(size))
        tile = _ICON.get(key)
        if tile is None:
            n = int(size); g = Image.new("RGB", (n, n))
            gd = ImageDraw.Draw(g)
            for k in range(n * 2):
                gd.line([(k, 0), (k - n, n)], fill=mix((250, 160, 40), mix((225, 48, 108), (131, 58, 180), (k / (2 * n) - 0.5) * 2), min(1, k / n)))
            tile = g.convert("RGBA"); tile.putalpha(_rmask(n, n, int(size * 0.26))); _ICON[key] = tile
        paste_rgba(img, tile, x0, y0, alpha)
    else:
        rr(img, (x0, y0, x0 + size, y0 + size), size * 0.26, fill=col, alpha=alpha)
        if col == (0, 0, 0) or col == (36, 41, 47):
            rr(img, (x0, y0, x0 + size, y0 + size), size * 0.26, outline=(80, 84, 100), width=2, alpha=alpha)
    ic = icon(glyph, size * 0.62, INK if app == "Dashboard" else WHITE)
    paste_rgba(img, ic, cx - ic.width / 2, cy - ic.height / 2, alpha)

def cursor_img(size=34):
    key = ("__cursor", size)
    im = _ICON.get(key)
    if im is None:
        s = 4; S = size * s
        big = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(big)
        pts = [(2, 2), (2, 30), (9, 23), (14, 33), (19, 31), (14, 21), (24, 21)]
        sc = S / 34
        d.polygon([(x * sc, y * sc) for x, y in pts], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=int(2.2 * sc))
        im = _ICON[key] = big.resize((size, size), Image.LANCZOS)
    return im
