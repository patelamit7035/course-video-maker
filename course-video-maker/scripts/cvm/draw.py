"""Shared drawing pieces for scene types: theme palette, cards, chips, whiteboard, marker writing, the pen,
people (characters), speech bubbles, and cue timing."""
import math
from PIL import Image, ImageDraw
from core import *

# ------------------------------------------------------------------ theme
class Theme:
    def __init__(self, brand=None):
        b = brand or {}
        self.light = b.get("theme", "dark") == "light"
        self.accent = hex_rgb(b.get("accent", "#FFB81C"))
        self.accent_ink = INK if sum(self.accent) > 380 else WHITE
        if self.light:
            self.bg0, self.bg1 = (246, 244, 238), (236, 234, 228)
            self.text, self.muted, self.card, self.card2, self.line = (26, 28, 38), (104, 108, 124), (255, 255, 255), (236, 238, 244), (214, 216, 226)
            self.grid = (0, 0, 0, 8)
        else:
            self.bg0, self.bg1 = (10, 11, 24), (16, 15, 42)
            self.text, self.muted, self.card, self.card2, self.line = WHITE, MUTED, CARD, CARD2, LINE
            self.grid = (255, 255, 255, 7)
        self.watermark = b.get("watermark", "")
        self.course = b.get("course", "")

def hex_rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

T = Theme()              # replaced by engine.load()

VX0, VY0, VX1, VY1 = 120, 236, 1800, 884          # visual area under the headline
VCX, VCY = (VX0 + VX1) / 2, (VY0 + VY1) / 2

BOARD = (250, 249, 244)
MARK = (34, 38, 52)
MBLUE = (40, 92, 200)
MRED = (214, 58, 58)
MGREEN = (34, 150, 84)
SOFT = [(255, 184, 28), (90, 160, 255), (52, 199, 120), (240, 96, 120), (170, 120, 250), (255, 140, 60), (40, 190, 200)]

def hand(s, bold=True): return font(HAND if bold else HAND_R, s)

def card(img, box, alpha=1.0, col=None, border="line", r=22):
    col = T.card if col is None else col
    rr(img, (box[0] + 4, box[1] + 10, box[2] + 4, box[3] + 14), r, fill=(0, 0, 0, 60 if T.light else 90), alpha=alpha)
    rr(img, box, r, fill=col, alpha=alpha)
    if border: rr(img, box, r, outline=T.line if border == "line" else border, width=2, alpha=alpha)

def chip(img, d, cx, cy, s, f, fg=None, bg=None, alpha=1.0, pad=26):
    fg = T.accent_ink if fg is None else fg; bg = T.accent if bg is None else bg
    h = f.size + 26; w = tw(f, s) + 2 * pad
    b = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
    rr(img, b, h / 2, fill=bg, alpha=alpha)
    text(d, (b[0] + pad, cy), s, f, A(fg, 255 * alpha), "lm")
    return b

# ------------------------------------------------------------------ cue timing
def cue_frac(scene, cue, default):
    """Fraction of the scene's voice at which a word is spoken (from its position in the text)."""
    if not cue: return default
    vo = scene.get("vo", "").lower(); i = vo.find(str(cue).lower())
    if i < 0: return default
    return clamp(i / max(1, len(vo)) * 0.96)

def item_times(scene, items, start=0.08, span=0.78):
    n = max(1, len(items)); out = []
    for k, it in enumerate(items):
        default = start + k * (span / n)
        if isinstance(it, dict):
            if "at" in it: out.append(float(it["at"])); continue
            out.append(cue_frac(scene, it.get("cue"), default))
        else: out.append(default)
    if out and min(out) > 0.2:          # cards never start blank: the first item shows early, the rest keep their cue
        k = out.index(min(out)); out[k] = 0.08
    return out

def txt(it, key="text"):
    return it.get(key, "") if isinstance(it, dict) else str(it)

# ------------------------------------------------------------------ whiteboard
def board(img, box=None, alpha=1.0):
    b = box or (VX0 - 30, VY0 - 6, VX1 + 30, VY1 + 30)
    rr(img, (b[0] + 6, b[1] + 12, b[2] + 6, b[3] + 16), 26, fill=(0, 0, 0, 110), alpha=alpha)
    rr(img, (b[0] - 14, b[1] - 14, b[2] + 14, b[3] + 14), 30, fill=(150, 156, 170), alpha=alpha)
    rr(img, b, 22, fill=BOARD, alpha=alpha)
    rr(img, (b[0] + 60, b[3] + 2, b[0] + 360, b[3] + 16), 6, fill=(120, 126, 140), alpha=alpha)
    for k, col in enumerate((MARK, MRED, MBLUE)):
        rr(img, (b[0] + 80 + k * 90, b[3] - 4, b[0] + 150 + k * 90, b[3] + 8), 5, fill=col, alpha=alpha)
    return b

def write_hand(d, xy, s, f, col, p, anchor="la"):
    if p <= 0: return
    n = max(1, int(round(len(s) * clamp(p))))
    if anchor[0] == "m": xy = (xy[0] - tw(f, s) / 2, xy[1]); anchor = "l" + anchor[1]
    elif anchor[0] == "r": xy = (xy[0] - tw(f, s), xy[1]); anchor = "l" + anchor[1]
    text(d, xy, s[:n], f, A(col, 255), anchor)

def pen(img, x, y, col=MARK):
    m = Image.new("RGBA", (220, 220), (0, 0, 0, 0)); md = ImageDraw.Draw(m); ox, oy = 10, 160
    md.polygon([(ox + 20, oy - 32), (ox + 74, oy - 116), (ox + 104, oy - 96), (ox + 48, oy - 14)], fill=(240, 240, 246, 255))
    md.polygon([(ox, oy), (ox + 20, oy - 32), (ox + 48, oy - 14)], fill=tuple(col) + (255,))
    md.polygon([(ox + 74, oy - 116), (ox + 84, oy - 132), (ox + 114, oy - 112), (ox + 104, oy - 96)], fill=tuple(col) + (255,))
    img.paste(m, (int(x - ox), int(y - oy)), m)

def wipe_paste(img, layer, x, y, p, with_pen=True, pen_col=MARK):
    """Reveal an RGBA drawing left to right, as if drawn, with the marker riding the edge."""
    if p <= 0: return
    if p >= 1: img.paste(layer, (int(x), int(y)), layer); return
    w, h = layer.size; cut = max(1, int(w * ease(p)))
    part = layer.crop((0, 0, cut, h)); img.paste(part, (int(x), int(y)), part)
    if with_pen:
        bbox = layer.getchannel("A").crop((max(0, cut - 3), 0, cut, h)).getbbox()
        py = y + (bbox[1] + bbox[3]) / 2 if bbox else y + h / 2
        pen(img, x + cut, py, pen_col)

def sketch_box(dd, box, col=MARK, width=6, fill=None, seed=0):
    """A hand-drawn rectangle (slightly wobbly lines)."""
    x0, y0, x1, y1 = box
    rnd = [((seed * 37 + k * 17) % 11 - 5) * 0.8 for k in range(8)]
    if fill: dd.rounded_rectangle(box, 18, fill=fill)
    pts = [(x0 + rnd[0], y0 + rnd[1]), (x1 + rnd[2], y0 + rnd[3]), (x1 + rnd[4], y1 + rnd[5]), (x0 + rnd[6], y1 + rnd[7]), (x0 + rnd[0], y0 + rnd[1] + 2)]
    dd.line(pts, fill=col, width=width, joint="curve")

def sketch_arrow(dd, a, b, col=MARK, width=6):
    dd.line([a, b], fill=col, width=width)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    for s in (2.6, -2.6):
        dd.line([b, (b[0] + 26 * math.cos(ang + s), b[1] + 26 * math.sin(ang + s))], fill=col, width=width)

# ------------------------------------------------------------------ people
SKIN = {"light": (232, 186, 150), "medium": (204, 146, 112), "dark": (150, 100, 70)}
def person(img, cx, cy, h, look=None, mood="happy", pose="stand", alpha=1.0, wave_arm=0.0):
    """A flat character. look = {gender: female|male, skin: light|medium|dark, hair: '#hex', outfit: '#hex'}.
    cy = chin line, h = head-to-waist scale. mood: happy|worried|thinking|excited. pose: stand|sit|point."""
    lk = look or {}
    female = lk.get("gender", "female") == "female"
    SK = SKIN.get(lk.get("skin", "medium"), SKIN["medium"])
    HAIR = hex_rgb(lk.get("hair", "#1e181c"))
    KU = hex_rgb(lk.get("outfit", "#18968f" if female else "#3b6fd8"))
    KU2 = tuple(max(0, c - 30) for c in KU)
    u = h / 100.0
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(lay)
    hx, hy = cx, cy - 22 * u
    if female: g.rounded_rectangle([hx - 26 * u, hy - 24 * u, hx + 26 * u, hy + 44 * u], 22 * u, fill=HAIR)
    bottom = cy + (70 if pose == "sit" else 150) * u
    g.polygon([(cx - 46 * u, bottom), (cx - 36 * u, cy + 14 * u), (cx - 12 * u, cy + 4 * u), (cx + 12 * u, cy + 4 * u),
               (cx + 36 * u, cy + 14 * u), (cx + 46 * u, bottom)], fill=KU)
    g.polygon([(cx - 12 * u, cy + 4 * u), (cx, cy + 22 * u), (cx + 12 * u, cy + 4 * u)], fill=SK)
    if female:
        g.line([(cx, cy + 22 * u), (cx, cy + 60 * u)], fill=KU2, width=max(2, int(3 * u)))
        g.polygon([(cx - 36 * u, cy + 14 * u), (cx - 18 * u, cy + 8 * u), (cx + 30 * u, cy + 70 * u), (cx + 16 * u, cy + 78 * u)], fill=(255, 196, 70))
    else:
        g.polygon([(cx - 12 * u, cy + 4 * u), (cx - 4 * u, cy + 24 * u), (cx - 18 * u, cy + 14 * u)], fill=(250, 250, 250))
        g.polygon([(cx + 12 * u, cy + 4 * u), (cx + 4 * u, cy + 24 * u), (cx + 18 * u, cy + 14 * u)], fill=(250, 250, 250))
        for k in range(3): g.ellipse([cx - 2 * u, cy + (34 + k * 16) * u, cx + 2 * u, cy + (38 + k * 16) * u], fill=KU2)
    if pose != "sit":
        g.line([(cx - 38 * u, cy + 20 * u), (cx - 50 * u, cy + 80 * u)], fill=KU, width=int(14 * u))
        g.ellipse([cx - 57 * u, cy + 74 * u, cx - 43 * u, cy + 88 * u], fill=SK)
        ang = -0.9 - wave_arm * 0.6 if pose != "point" else -2.4
        ex, ey = cx + 38 * u + 32 * u * math.cos(ang + 1.6), cy + 20 * u + 32 * u * math.sin(ang + 1.6)
        g.line([(cx + 38 * u, cy + 20 * u), (ex, ey)], fill=KU, width=int(14 * u))
        g.ellipse([ex - 7 * u, ey - 7 * u, ex + 7 * u, ey + 7 * u], fill=SK)
    g.rectangle([hx - 7 * u, hy + 12 * u, hx + 7 * u, cy + 6 * u], fill=SK)
    g.ellipse([hx - 20 * u, hy - 24 * u, hx + 20 * u, hy + 24 * u], fill=SK)
    if female:
        g.chord([hx - 22 * u, hy - 27 * u, hx + 22 * u, hy + 8 * u], 180, 360, fill=HAIR)
        g.pieslice([hx - 22 * u, hy - 20 * u, hx + 4 * u, hy + 14 * u], 180, 270, fill=HAIR)
        for ex_ in (-21, 21): g.ellipse([hx + (ex_ - 2) * u, hy + 6 * u, hx + (ex_ + 2) * u, hy + 10 * u], fill=(255, 200, 60))
    else:
        g.chord([hx - 21 * u, hy - 27 * u, hx + 21 * u, hy - 2 * u], 180, 360, fill=HAIR)
        g.rectangle([hx - 21 * u, hy - 12 * u, hx - 16 * u, hy + 2 * u], fill=HAIR); g.rectangle([hx + 16 * u, hy - 12 * u, hx + 21 * u, hy + 2 * u], fill=HAIR)
    for ex_ in (-8, 8):
        g.ellipse([hx + (ex_ - 2.6) * u, hy, hx + (ex_ + 2.6) * u, hy + 5 * u], fill=(26, 22, 26))
        g.line([(hx + (ex_ - 5) * u, hy - 4.5 * u), (hx + (ex_ + 4) * u, hy - 5.5 * u)], fill=HAIR, width=max(1, int(1.6 * u)))
    if mood == "worried":
        g.arc([hx - 7 * u, hy + 12 * u, hx + 7 * u, hy + 20 * u], 200, 340, fill=(120, 50, 50), width=max(2, int(2 * u)))
        g.ellipse([hx + 20 * u, hy - 14 * u, hx + 25 * u, hy - 6 * u], fill=(120, 190, 255))
    elif mood == "thinking":
        g.line([(hx - 5 * u, hy + 15 * u), (hx + 6 * u, hy + 13 * u)], fill=(120, 50, 50), width=max(2, int(2 * u)))
    elif mood == "excited":
        g.chord([hx - 9 * u, hy + 6 * u, hx + 9 * u, hy + 20 * u], 0, 180, fill=(150, 50, 60))
    else:
        g.arc([hx - 8 * u, hy + 6 * u, hx + 8 * u, hy + 17 * u], 20, 160, fill=(150, 50, 60), width=max(2, int(2.2 * u)))
    if alpha < 1: lay.putalpha(lay.getchannel("A").point(lambda v: int(v * alpha)))
    img.paste(lay, (0, 0), lay)

def bubble(img, d, box, s, p, tail=(0, 0), col=WHITE, ink=INK, f=None, typed=1.0):
    """A speech bubble whose text types in (typed = 0..1)."""
    if p <= 0: return
    f = f or fs(38)
    rr(img, box, 28, fill=col, alpha=p)
    tx, ty = tail
    if tx or ty:
        m = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(m).polygon(
            [(box[0] + 60, box[3] - 2), (box[0] + 120, box[3] - 2), (tx, ty)], fill=tuple(col) + (int(255 * p),))
        img.paste(m, (0, 0), m)
    lines = wrap(s, f, box[2] - box[0] - 70); n = int(sum(len(l) for l in lines) * clamp(typed))
    for k, ln in enumerate(lines):
        text(d, (box[0] + 35, box[1] + 40 + k * (f.size + 14)), ln[:max(0, n)], f, A(ink, 255 * p), "lm"); n -= len(ln)
