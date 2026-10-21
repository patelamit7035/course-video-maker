"""Scene types. Each: fn(img, d, ck, scene, ctx). ck runs on the scene's voice: ck.f = 0 at the first word, 1 at the last.
Items can carry "cue": a word from the voiceover; the item appears when that word is spoken."""
import math, os
from PIL import Image, ImageDraw, ImageOps
import draw as D
from draw import VX0, VY0, VX1, VY1, VCX, VCY, card, chip, cue_frac, item_times, txt, board, write_hand, hand, wipe_paste, \
    sketch_box, sketch_arrow, person, bubble, MARK, MBLUE, MRED, MGREEN, BOARD, SOFT
from core import *

def T(): return D.T

# ------------------------------------------------------------------ title
def t_title(img, d, ck, s, ctx):
    p = ck.ap(0.0, 0.5)
    t = s.get("title", ctx["title"])
    f = fit(t, "InterDisplay-Black.otf", 110, 1600)
    text(d, (VCX, VCY - 40 + (1 - ease(p)) * 20), t, f, A(T().text, 255 * p), "mm")
    wv = tw(f, t); rr(img, (VCX - wv / 2, VCY + 40, VCX - wv / 2 + wv * ease(ck.ap(0.1, 0.6)), VCY + 50), 5, fill=T().accent)
    if s.get("subtitle"):
        q = ck.ap(0.25, 0.5); text(d, (VCX, VCY + 120), s["subtitle"], fit(s["subtitle"], "Inter-SemiBold.otf", 44, 1500), A(T().muted, 255 * q), "mm")

# ------------------------------------------------------------------ slides
def t_slides(img, d, ck, s, ctx):
    items = s.get("bullets", []); at = item_times(s, items, 0.06, 0.8)
    b = (VX0 + 60, VY0 - 10, VX1 - 60, VY1 + 20)
    card(img, b, 1.0)
    rr(img, (b[0], b[1], b[0] + 14, b[3]), 7, fill=T().accent)
    y0 = b[1] + 60
    if s.get("title"):
        text(d, (b[0] + 70, y0), s["title"], fit(s["title"], "InterDisplay-ExtraBold.otf", 56, b[2] - b[0] - 140), T().text, "lm"); y0 += 100
    rh = min(110, (b[3] - y0 - 30) / max(1, len(items)))
    for k, it in enumerate(items):
        p = ck.ap(at[k], 0.35)
        if p <= 0: continue
        y = y0 + k * rh + rh / 2 - 20 + (1 - ease(p)) * 16
        cur = k == max([j for j in range(len(items)) if ck.f >= at[j]] or [0])
        ic = it.get("icon") if isinstance(it, dict) else None
        circle(img, b[0] + 100, y, 30, fill=T().accent if cur else T().card2, alpha=p)
        if ic: paste_rgba(img, icon(ic, 34, T().accent_ink if cur else T().text), b[0] + 83, y - 17, p)
        else: text(d, (b[0] + 100, y), str(k + 1), fb(28), A(T().accent_ink if cur else T().text, 255 * p), "mm")
        st = txt(it); f = fit(st, "Inter-SemiBold.otf", 46, b[2] - b[0] - 240)
        text(d, (b[0] + 160, y), st, f, A(T().text if cur else T().muted, 255 * p), "lm")

# ------------------------------------------------------------------ kinetic text
def t_kinetic(img, d, ck, s, ctx):
    lines = s.get("lines", []); at = item_times(s, lines, 0.05, 0.75); n = len(lines)
    cols = {"accent": T().accent, "red": RED, "green": GREEN, "muted": T().muted, "normal": T().text}
    y0 = VCY - (n - 1) * 80
    for k, ln in enumerate(lines):
        p = ck.ap(at[k], 0.35)
        if p <= 0: continue
        style = ln.get("style", "normal") if isinstance(ln, dict) else "normal"
        c = cols.get(style, T().text) if style != "strike" else T().muted
        st = txt(ln); f = fit(st, "InterDisplay-Black.otf", 96 if n <= 2 else 78, 1500)
        y = y0 + k * 160; sc = back(p); ic = ln.get("icon") if isinstance(ln, dict) else None
        wtxt = tw(f, st) + (120 if ic else 0); x0 = VCX - wtxt / 2
        if ic:
            circle(img, x0 + 44, y, 50 * sc, fill=A(c, 45), alpha=p)
            paste_rgba(img, icon(ic, int(60 * sc), c), x0 + 44 - 30 * sc, y - 30 * sc, p)
        text(d, (x0 + (120 if ic else 0), y + (1 - ease(p)) * 24), st, f, A(c, 255 * p), "lm")
        if style == "strike":
            q = clamp((ck.f - at[k] - 0.12) / 0.1)
            if q > 0: d.line([(x0 + (110 if ic else -10), y), (x0 + (110 if ic else -10) + (wtxt - (100 if ic else -20)) * ease(q), y)], fill=A(RED, 230), width=9)

# ------------------------------------------------------------------ icons grid
def t_icons(img, d, ck, s, ctx):
    items = s.get("items", []); at = item_times(s, items, 0.05, 0.8); n = len(items)
    cols = min(4, n) if n != 5 else 5; rows = math.ceil(n / cols)
    cw = (VX1 - VX0) / cols; chh = (VY1 - VY0 + 40) / rows
    for k, it in enumerate(items):
        p = ck.ap(at[k], 0.35)
        if p <= 0: continue
        cx = VX0 + (k % cols + 0.5) * cw; cy = VY0 + (k // cols + 0.5) * chh - 10
        sc = back(p); r = 92 * sc; col = SOFT[k % len(SOFT)]
        circle(img, cx, cy - 40, r, fill=A(col, 50), alpha=p); circle(img, cx, cy - 40, r - 14, fill=col, alpha=p)
        paste_rgba(img, icon(it.get("icon", "star"), int(90 * sc), WHITE), cx - 45 * sc, cy - 40 - 45 * sc, p)
        lab = it.get("label", ""); f = fit(lab, "Inter-Bold.otf", 40, cw - 30)
        text(d, (cx, cy + 90), lab, f, A(T().text, 255 * p), "mm")

# ------------------------------------------------------------------ chart
def t_chart(img, d, ck, s, ctx):
    labels, vals = s.get("labels", []), [float(v) for v in s.get("values", [])]
    kind = s.get("chart", "bar"); unit = s.get("unit", ""); hi = s.get("highlight")
    b = (VX0 + 60, VY0 - 10, VX1 - 60, VY1 + 20); card(img, b, 1.0)
    if s.get("title"): text(d, (b[0] + 50, b[1] + 50), s["title"], fb(36), T().text, "lm")
    gx0, gy0, gx1, gy1 = b[0] + 120, b[1] + 110, b[2] - 60, b[3] - 90
    vmax = max(vals + [1]) * 1.15; grow = ease(clamp((ck.f - 0.05) / 0.5))
    if kind == "pie":
        cx, cy, r = (gx0 + gx1) / 2 - 250, (gy0 + gy1) / 2, min(gy1 - gy0, 500) / 2
        tot = sum(vals) or 1; a0 = -90
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(lay)
        for k, v in enumerate(vals):
            a1 = a0 + 360 * v / tot * grow
            g.pieslice([cx - r, cy - r, cx + r, cy + r], a0, a1, fill=SOFT[k % len(SOFT)] + (255,)); a0 = a1
        img.paste(lay, (0, 0), lay)
        for k, (lab, v) in enumerate(zip(labels, vals)):
            q = ck.ap(0.5 + k * 0.06, 0.3); y = gy0 + 40 + k * 70
            rr(img, (cx + r + 80, y - 16, cx + r + 112, y + 16), 6, fill=SOFT[k % len(SOFT)], alpha=q)
            text(d, (cx + r + 130, y), f"{lab}  {v:g}{unit}", fs(34), A(T().text, 255 * q), "lm")
        return
    d.line([(gx0, gy1), (gx1, gy1)], fill=A(T().muted, 200), width=3)
    n = len(vals)
    if kind == "line":
        pts = [(gx0 + k / max(1, n - 1) * (gx1 - gx0), gy1 - v / vmax * (gy1 - gy0)) for k, v in enumerate(vals)]
        m = grow * (n - 1); shown = [pts[0]]
        for k in range(1, n):
            if m >= k: shown.append(pts[k])
            elif m > k - 1:
                fr_ = m - (k - 1); shown.append((lerp(pts[k - 1][0], pts[k][0], fr_), lerp(pts[k - 1][1], pts[k][1], fr_)))
        if len(shown) > 1: d.line(shown, fill=A(T().accent, 255), width=8, joint="curve")
        for k, (x, y) in enumerate(pts):
            if m >= k:
                circle(img, x, y, 12, fill=RED if hi == k else T().accent)
                text(d, (x, y - 40), f"{vals[k]:g}{unit}", fb(30), T().text, "mm")
            text(d, (x, gy1 + 36), labels[k] if k < len(labels) else "", fs(28), T().muted, "mm")
        return
    bw = (gx1 - gx0) / n * 0.6
    for k, v in enumerate(vals):
        q = ease(clamp((ck.f - 0.05 - k * 0.06) / 0.25))
        x = gx0 + (k + 0.5) * (gx1 - gx0) / n; hgt = v / vmax * (gy1 - gy0) * q
        col = (RED if s.get("highlight_color") == "red" else T().accent) if hi == k else SOFT[1]
        rr(img, (x - bw / 2, gy1 - hgt, x + bw / 2, gy1), 10, fill=col)
        if q > 0.5: text(d, (x, gy1 - hgt - 30), f"{v:g}{unit}", fb(34), T().text, "mm")
        text(d, (x, gy1 + 36), labels[k] if k < len(labels) else "", fit(labels[k] if k < len(labels) else "", "Inter-SemiBold.otf", 30, (gx1 - gx0) / n), T().muted, "mm")
    if s.get("note"):
        q = ck.ap(0.7, 0.4); fn = fb(28); chip(img, d, b[2] - 50 - (tw(fn, s["note"]) + 52) / 2, b[1] + 50, s["note"], fn, alpha=q)

# ------------------------------------------------------------------ whiteboard
def t_whiteboard(img, d, ck, s, ctx):
    b = board(img)
    lay = s.get("layout", "list"); items = s.get("items", []); at = item_times(s, items, 0.12, 0.75)
    title = s.get("title", "")
    if title: write_hand(d, (b[0] + 70, b[1] + 78), title, hand(66), MARK, clamp(ck.f / 0.1), "lm")
    if title:
        q = clamp((ck.f - 0.08) / 0.06); tw_ = tw(hand(66), title)
        if q > 0: d.line([(b[0] + 70, b[1] + 128), (b[0] + 70 + tw_ * ease(q), b[1] + 132)], fill=MRED, width=6)
    top = b[1] + (160 if title else 80)
    if lay == "list":
        for k, it in enumerate(items):
            q = clamp((ck.f - at[k]) / 0.12)
            if q <= 0: continue
            y = top + 30 + k * 100
            t1 = clamp(q / 0.3); d.line([(b[0] + 90, y), (b[0] + 90 + 14 * t1, y + 16 * t1)], fill=MGREEN, width=8)
            if q > 0.3:
                t2 = clamp((q - 0.3) / 0.3); d.line([(b[0] + 104, y + 16), (b[0] + 104 + 26 * t2, y + 16 - 36 * t2)], fill=MGREEN, width=8)
            st = txt(it); f = font(D.HAND, min(58, int(58 * 1500 / max(1500, tw(hand(58), st)))))
            write_hand(d, (b[0] + 160, y), st, f, MBLUE if k % 2 else MARK, clamp((q - 0.2) / 0.6), "lm")
            ic = it.get("icon") if isinstance(it, dict) else None
            if ic and q > 0.5: paste_rgba(img, icon(ic, 64, MRED), b[2] - 140, y - 32, clamp((q - 0.5) / 0.3))
    elif lay in ("flow", "steps"):
        n = len(items); gap = 70; bw = min(440, ((b[2] - b[0] - 120) - gap * (n - 1)) / n); bh = 270
        x0 = (b[0] + b[2]) / 2 - (n * bw + (n - 1) * gap) / 2; y0 = (top + b[3]) / 2 - bh / 2
        for k, it in enumerate(items):
            q = clamp((ck.f - at[k]) / 0.12)
            if q <= 0: continue
            x = x0 + k * (bw + gap)
            L = Image.new("RGBA", (int(bw + 10), int(bh + 10)), (0, 0, 0, 0)); ld = ImageDraw.Draw(L)
            sketch_box(ld, (5, 5, bw, bh), MARK, 6, fill=(255, 244, 214) if k % 2 == 0 else (226, 238, 255), seed=k)
            wipe_paste(img, L, x, y0, clamp(q / 0.5))
            ic = it.get("icon") if isinstance(it, dict) else None
            if ic and q > 0.4: paste_rgba(img, icon(ic, 70, MBLUE), x + bw / 2 - 35, y0 + 30, clamp((q - 0.4) / 0.3))
            st = txt(it); f = hand(50 if len(st) < 14 else 42)
            lines = wrap(st, f, bw - 30)
            for j, ln in enumerate(lines[:3]):
                write_hand(d, (x + bw / 2, y0 + (150 if ic else bh / 2 - (len(lines) - 1) * 26) + j * 54), ln, f, MARK, clamp((q - 0.45) / 0.4), "mm")
            if k < n - 1 and q > 0.8:
                L2 = Image.new("RGBA", (gap + 20, 60), (0, 0, 0, 0)); sketch_arrow(ImageDraw.Draw(L2), (6, 30), (gap + 6, 30), MRED, 6)
                wipe_paste(img, L2, x + bw, y0 + bh / 2 - 30, clamp((q - 0.8) / 0.2), with_pen=False)
    elif lay == "mindmap":
        cx, cy = (b[0] + b[2]) / 2, (top + b[3]) / 2 + 10
        p0 = clamp(ck.f / 0.1)
        L = Image.new("RGBA", (380, 170), (0, 0, 0, 0)); ld = ImageDraw.Draw(L)
        ld.ellipse([6, 6, 372, 162], fill=(255, 236, 190), outline=MARK, width=7)
        wipe_paste(img, L, cx - 190, cy - 85, p0)
        write_hand(d, (cx, cy), s.get("center", ""), hand(52), MARK, clamp((ck.f - 0.06) / 0.1), "mm")
        n = len(items)
        for k, it in enumerate(items):
            q = clamp((ck.f - at[k]) / 0.12)
            if q <= 0: continue
            ang = -math.pi / 2 + k * 2 * math.pi / n
            ex, ey = cx + 560 * math.cos(ang), cy + 240 * math.sin(ang)
            sx, sy = cx + 200 * math.cos(ang), cy + 95 * math.sin(ang)
            hf = hand(44); hw, hh = tw(hf, txt(it)) / 2 + 26, 44
            dx, dy = ex - sx, ey - sy
            tcut = min([hw / abs(dx) if abs(dx) > 1 else 9, hh / abs(dy) if abs(dy) > 1 else 9])
            tt = clamp(1 - tcut, 0.25, 0.85); lx, ly = lerp(sx, ex, tt), lerp(sy, ey, tt)
            d.line([(sx, sy), (lerp(sx, lx, ease(clamp(q / 0.4))), lerp(sy, ly, ease(clamp(q / 0.4))))], fill=MBLUE, width=6)
            write_hand(d, (ex, ey), txt(it), hand(44), MRED if k % 2 else MARK, clamp((q - 0.35) / 0.5), "mm")
    elif lay == "compare":
        mid = (b[0] + b[2]) / 2
        d.line([(mid, top), (mid, b[3] - 40)], fill=A(MARK, int(255 * clamp(ck.f / 0.1))), width=5)
        for side, key, col in ((0, "left", MRED), (1, "right", MGREEN)):
            blk = s.get(key, {}); x = b[0] + 80 + side * ((b[2] - b[0]) / 2)
            p = clamp((ck.f - cue_frac(s, blk.get("cue"), 0.1 + side * 0.45)) / 0.1)
            write_hand(d, (x, top + 30), blk.get("title", ""), hand(56), col, p)
            for j, pt in enumerate(blk.get("points", [])):
                q = clamp((ck.f - cue_frac(s, pt.get("cue") if isinstance(pt, dict) else None, 0.15 + side * 0.45 + (j + 1) * 0.08)) / 0.1)
                write_hand(d, (x, top + 120 + j * 80), "- " + txt(pt), hand(44, False), MARK, q)
    elif lay == "equation":
        n = len(items); parts = []
        for k, it in enumerate(items):
            parts.append(txt(it))
            if k < n - 1: parts.append("=" if k == n - 2 else "+")
        f = hand(70); total = sum(tw(f, p_) + 50 for p_ in parts); x = (b[0] + b[2]) / 2 - total / 2; y = (top + b[3]) / 2
        for j, p_ in enumerate(parts):
            k = j // 2; q = clamp((ck.f - at[min(k + (1 if j % 2 else 0), n - 1)] + (0.02 if j % 2 else 0)) / 0.1)
            col = MBLUE if j % 2 == 0 and j < len(parts) - 1 else (MRED if j == len(parts) - 1 else MARK)
            write_hand(d, (x, y), p_, f, col, q, "lm"); x += tw(f, p_) + 50

# ------------------------------------------------------------------ character story
PLACES = {"class": ((232, 240, 250), "board"), "office": ((236, 240, 236), "window"), "home": ((250, 238, 226), "sofa"),
          "shop": ((252, 244, 222), "shelf"), "none": (None, None)}
def t_character(img, d, ck, s, ctx):
    pl = s.get("place", "none"); bgc, prop = PLACES.get(pl, PLACES["none"])
    b = (VX0 - 20, VY0 - 10, VX1 + 20, VY1 + 30)
    if bgc:
        rr(img, b, 26, fill=bgc)
        rr(img, (b[0], b[3] - 120, b[2], b[3]), 26, fill=tuple(max(0, c - 30) for c in bgc))
        if prop == "board":
            rr(img, (b[0] + 120, b[1] + 60, b[0] + 620, b[1] + 360), 14, fill=(40, 70, 60)); write_hand(d, (b[0] + 160, b[1] + 120), s.get("board_text", ""), hand(48), WHITE, 1.0, "lm")
        elif prop == "window":
            rr(img, (b[0] + 120, b[1] + 60, b[0] + 520, b[1] + 330), 10, fill=(190, 220, 245)); d.line([(b[0] + 320, b[1] + 60), (b[0] + 320, b[1] + 330)], fill=WHITE, width=8)
        elif prop == "sofa":
            rr(img, (b[0] + 100, b[3] - 290, b[0] + 560, b[3] - 140), 30, fill=(170, 110, 90))
        elif prop == "shelf":
            for k in range(3): rr(img, (b[0] + 100, b[1] + 80 + k * 110, b[0] + 560, b[1] + 96 + k * 110), 4, fill=(150, 110, 70))
    pe = s.get("person", {}); mood = s.get("mood", "happy")
    if s.get("mood_after") and ck.f > s.get("mood_change_at", 0.55): mood = s["mood_after"]
    p = ck.ap(0.0, 0.5)
    px = VX0 + 860 if s.get("say") else VCX
    person(img, px, VY0 + 230, 300, pe.get("look"), mood, s.get("pose", "stand"), alpha=p, wave_arm=0.5 + 0.5 * math.sin(ck.t * 3))
    if pe.get("name"): chip(img, d, px, VY1 - 10, pe["name"], fb(32), alpha=p)
    if s.get("say"):
        q = ck.ap(0.1, 0.35)
        bubble(img, d, (VX0 + 1060, VY0 + 20, VX1 - 20, VY0 + 330), s["say"], q, tail=(px + 80, VY0 + 160), typed=clamp((ck.f - 0.12) / 0.5))
    for k, tg in enumerate(s.get("tags", [])):
        at = cue_frac(s, tg.get("cue") if isinstance(tg, dict) else None, 0.3 + k * 0.2)
        q = ck.ap(at, 0.35)
        if q > 0: chip(img, d, VX1 - 300, VY0 + 420 + k * 100, txt(tg), fb(32), WHITE if k else None, T().card2 if k else None, q)

# ------------------------------------------------------------------ flow / timeline
def t_flow(img, d, ck, s, ctx):
    steps = s.get("steps", []); at = item_times(s, steps, 0.06, 0.78); n = len(steps)
    if s.get("mode") == "timeline":
        y = VCY + 20; x0, x1 = VX0 + 60, VX1 - 60
        g = ease(clamp(ck.f / 0.8)); rr(img, (x0, y - 5, x0 + (x1 - x0) * g, y + 5), 5, fill=T().line)
        for k, st in enumerate(steps):
            p = ck.ap(at[k], 0.35)
            if p <= 0: continue
            x = x0 + (k + 0.5) / n * (x1 - x0); up = k % 2 == 0
            circle(img, x, y, 22 * back(p), fill=T().accent)
            bx = (x - 170, (y - 270) if up else (y + 60), x + 170, (y - 60) if up else (y + 270))
            card(img, bx, p)
            text(d, (x, bx[1] + 55), st.get("title", ""), fit(st.get("title", ""), "Inter-Bold.otf", 36, 310), A(T().text, 255 * p), "mm")
            for j, ln in enumerate(wrap(st.get("sub", ""), fs(26), 300)[:3]): text(d, (x, bx[1] + 105 + j * 34), ln, fs(26), A(T().muted, 255 * p), "mm")
        return
    gap = 60; bw = min(360, (VX1 - VX0 - gap * (n - 1)) / n); bh = 340
    x0 = VCX - (n * bw + (n - 1) * gap) / 2; y0 = VCY - bh / 2 + 20
    cur = max([k for k in range(n) if ck.f >= at[k]] or [0])
    for k, st in enumerate(steps):
        p = ck.ap(at[k], 0.35)
        if p <= 0: continue
        x = x0 + k * (bw + gap); on = k == cur
        bx = (x, y0 + (1 - ease(p)) * 30, x + bw, y0 + bh + (1 - ease(p)) * 30)
        card(img, bx, p, border=T().accent if on else "line")
        circle(img, x + bw / 2, bx[1] + 80, 52, fill=T().accent if on else T().card2, alpha=p)
        if st.get("icon"): paste_rgba(img, icon(st["icon"], 56, T().accent_ink if on else T().text), x + bw / 2 - 28, bx[1] + 52, p)
        else: text(d, (x + bw / 2, bx[1] + 80), str(k + 1), fk(48), A(T().accent_ink if on else T().text, 255 * p), "mm")
        text(d, (x + bw / 2, bx[1] + 175), st.get("title", ""), fit(st.get("title", ""), "Inter-Bold.otf", 38, bw - 30), A(T().text, 255 * p), "mm")
        for j, ln in enumerate(wrap(st.get("sub", ""), fs(26), bw - 40)[:3]): text(d, (x + bw / 2, bx[1] + 225 + j * 34), ln, fs(26), A(T().muted, 255 * p), "mm")
        if k < n - 1 and ck.f > at[k] + 0.05:
            q = clamp((ck.f - at[k] - 0.05) / 0.08); ax = x + bw + 8
            d.line([(ax, VCY + 20), (ax + (gap - 16) * ease(q), VCY + 20)], fill=A(T().accent, 255 * q), width=6)
            if q > 0.9: d.polygon([(ax + gap - 16, VCY + 8), (ax + gap - 4, VCY + 20), (ax + gap - 16, VCY + 32)], fill=A(T().accent, 255))

# ------------------------------------------------------------------ software UI mock-up
def t_ui(img, d, ck, s, ctx):
    phone = s.get("device") == "phone"
    els = s.get("elements", [])
    if phone:
        b = (VCX - 210, VY0 - 20, VCX + 210, VY1 + 40)
        rr(img, (b[0] - 16, b[1] - 16, b[2] + 16, b[3] + 16), 60, fill=(20, 20, 24)); rr(img, b, 46, fill=UI_BG)
        x0, y = b[0] + 30, b[1] + 70; cw = b[2] - b[0] - 60
    else:
        b = (VX0 + 20, VY0 - 20, VX1 - 20, VY1 + 40)
        rr(img, (b[0] + 6, b[1] + 14, b[2] + 6, b[3] + 18), 22, fill=(0, 0, 0, 100)); rr(img, b, 18, fill=UI_BG)
        rr(img, (b[0], b[1], b[2], b[1] + 52), 18, fill=(232, 234, 240))
        for k, c in enumerate((RED, AMBER, GREEN)): circle(img, b[0] + 30 + k * 28, b[1] + 26, 8, fill=c)
        rr(img, (b[0] + 150, b[1] + 12, b[0] + 760, b[1] + 40), 14, fill=WHITE)
        text(d, (b[0] + 170, b[1] + 26), s.get("url", "yourapp.com"), fs(20), UI_MUTED, "lm")
        x0, y = b[0] + 70, b[1] + 100; cw = b[2] - b[0] - 140
    clicks = s.get("clicks", [])
    click_t = {c["i"] if isinstance(c, dict) else c: cue_frac(s, c.get("cue") if isinstance(c, dict) else None, 0.3 + k * 0.25) for k, c in enumerate(clicks)}
    boxes = {}
    for i, el in enumerate(els):
        k = el.get("kind", "text"); t_ = el.get("text", "")
        if k == "title": text(d, (x0, y + 28), t_, fb(54 if not phone else 34), UI_TEXT, "lm"); y += 90
        elif k == "text":
            for ln in wrap(t_, fr(32), cw): text(d, (x0, y + 20), ln, fr(32), UI_MUTED, "lm"); y += 46
            y += 10
        elif k == "field":
            text(d, (x0, y + 14), t_, fs(30), UI_TEXT, "lm"); y += 44
            fb_ = (x0, y, x0 + cw, y + 76); rr(img, fb_, 12, fill=WHITE); rr(img, fb_, 12, outline=UI_LINE, width=3)
            v = el.get("value", ""); tt = el.get("type_at")
            if tt is not None: v = v[:int(len(v) * clamp((ck.f - cue_frac(s, tt if isinstance(tt, str) else None, tt if isinstance(tt, (int, float)) else 0.3)) / 0.25))]
            text(d, (x0 + 22, y + 38), v, fit(v, "Inter-SemiBold.otf", 34, cw - 40), UI_TEXT, "lm"); boxes[i] = fb_; y += 100
        elif k == "button":
            bw_ = cw if el.get("wide") else tw(fs(32), t_) + 90; bb = (x0, y, x0 + bw_, y + 76)
            col = hex_rgb_safe(el.get("color"), (37, 99, 235))
            rr(img, bb, 14, fill=col); text(d, ((bb[0] + bb[2]) / 2, y + 38), t_, fs(32), WHITE, "mm"); boxes[i] = bb; y += 100
        elif k == "card":
            cb = (x0, y, x0 + cw, y + 110); rr(img, cb, 14, fill=UI_SIDE); rr(img, cb, 14, outline=UI_LINE, width=2)
            text(d, (x0 + 24, y + 38), t_, fs(28), UI_TEXT, "lm"); text(d, (x0 + 24, y + 76), el.get("value", ""), fr(24), UI_MUTED, "lm"); boxes[i] = cb; y += 130
        elif k == "toast":
            at = cue_frac(s, el.get("cue"), 0.85); q = ck.ap(at, 0.3)
            if q > 0:
                tb = (x0, y, x0 + cw, y + 80); rr(img, tb, 14, fill=(230, 248, 236), alpha=q)
                paste_rgba(img, icon("check", 40, GREEN), x0 + 22, y + 20, q); text(d, (x0 + 80, y + 40), t_, fs(34), A(UI_TEXT, 255 * q), "lm")
            y += 84
    # cursor flying to each clicked element, highlight box while it is clicked
    order = sorted(click_t.items(), key=lambda kv: kv[1]); pos = (b[2] - 120, b[3] - 120)
    for i, t0 in order:
        if i not in boxes: continue
        bx = boxes[i]; tgt = ((bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2)
        if ck.f >= t0 - 0.12:
            m = ease(clamp((ck.f - (t0 - 0.12)) / 0.12)); pos = (lerp(pos[0], tgt[0], m), lerp(pos[1], tgt[1], m))
            if ck.f >= t0 - 0.02: glow(img, bx, 12, col=AMBER, alpha=clamp((ck.f - t0 + 0.02) / 0.05) * (1 - clamp((ck.f - t0 - 0.25) / 0.1)))
            if t0 <= ck.f < t0 + 0.04: circle(img, tgt[0], tgt[1], 30, fill=(255, 184, 28, 90))
        else: break
    paste_rgba(img, cursor_img(40), pos[0], pos[1])

def hex_rgb_safe(h, default):
    try: return D.hex_rgb(h) if h else default
    except Exception: return default

# ------------------------------------------------------------------ chat conversation
def t_chat(img, d, ck, s, ctx):
    msgs = s.get("messages", []); at = item_times(s, msgs, 0.04, 0.85)
    b = (VCX - 330, VY0 - 30, VCX + 330, VY1 + 40)
    rr(img, (b[0] - 14, b[1] - 14, b[2] + 14, b[3] + 14), 56, fill=(20, 20, 24)); rr(img, b, 44, fill=(236, 229, 221))
    rr(img, (b[0], b[1], b[2], b[1] + 110), 44, fill=(0, 128, 105)); rr(img, (b[0], b[1] + 60, b[2], b[1] + 110), 0, fill=(0, 128, 105))
    circle(img, b[0] + 70, b[1] + 64, 26, fill=(220, 220, 220))
    text(d, (b[0] + 112, b[1] + 64), s.get("name", "Chat"), fb(30), WHITE, "lm")
    shown = [k for k in range(len(msgs)) if ck.f >= at[k]]
    heights = []
    for m in msgs:
        lines = wrap(m.get("text", ""), fs(32), 440); heights.append(34 + 44 * len(lines))
    total = sum(heights[k] + 18 for k in shown); avail = b[3] - b[1] - 150
    y = b[1] + 130 - max(0, total - avail)
    for k in shown:
        m = msgs[k]; me = m.get("from") == "me"; p = ck.ap(at[k], 0.25)
        lines = wrap(m.get("text", ""), fs(32), 440); w_ = max(tw(fs(32), l) for l in lines) + 48 if lines else 100
        x = b[2] - 30 - w_ if me else b[0] + 30
        if y > b[1] + 100:
            rr(img, (x, y, x + w_, y + heights[k]), 18, fill=(217, 253, 211) if me else WHITE, alpha=p)
            for j, ln in enumerate(lines): text(d, (x + 24, y + 39 + j * 44), ln, fs(32), A(UI_TEXT, 255 * p), "lm")
        y += heights[k] + 18

# ------------------------------------------------------------------ quiz
def t_quiz(img, d, ck, s, ctx):
    q0 = ck.ap(0.0, 0.4)
    text(d, (VCX, VY0 + 30), s.get("question", ""), fit(s.get("question", ""), "InterDisplay-ExtraBold.otf", 60, 1600), A(T().text, 255 * q0), "mm")
    opts = s.get("options", []); ans = s.get("answer", 0)
    rv = cue_frac(s, s.get("reveal_cue"), 0.75); rev = clamp((ck.f - rv) / 0.08)
    cols = 2; ow = 760; oh = 130
    for k, o in enumerate(opts):
        p = ck.ap(0.12 + k * 0.07, 0.3)
        if p <= 0: continue
        x = VCX - ow - 20 + (k % cols) * (ow + 40); y = VY0 + 140 + (k // cols) * (oh + 40)
        good = k == ans
        col = mix(T().card, (24, 120, 70) if good else (110, 40, 40), rev) if rev > 0 else T().card
        if not good and rev > 0: col = mix(T().card, T().card2, rev)
        card(img, (x, y, x + ow, y + oh), p, col=col, border=GREEN if (good and rev > 0) else "line")
        circle(img, x + 70, y + oh / 2, 36, fill=GREEN if (good and rev > 0) else T().accent, alpha=p)
        text(d, (x + 70, y + oh / 2), "ABCD"[k], fb(34), A(INK, 255 * p), "mm")
        text(d, (x + 130, y + oh / 2), o, fit(o, "Inter-SemiBold.otf", 40, ow - 170), A(T().text if (good or rev == 0) else T().muted, 255 * p), "lm")
        if good and rev > 0: paste_rgba(img, icon("check", 54, WHITE), x + ow - 80, y + oh / 2 - 27, rev)
    if ck.f < rv and ck.f > 0.4:
        q = ck.ap(0.4, 0.3); chip(img, d, VCX, VY1 + 10, "Pause and answer!", fb(32), alpha=q)

# ------------------------------------------------------------------ compare
def t_compare(img, d, ck, s, ctx):
    style = s.get("style", "wrong_right")
    names = {"wrong_right": ("WRONG", "RIGHT", RED, GREEN, "cross", "check"), "before_after": ("BEFORE", "AFTER", (150, 150, 170), GREEN, "clock", "star"),
             "vs": ("", "", SOFT[1], SOFT[0], "star", "star")}[style]
    for side, key in ((0, "left"), (1, "right")):
        blk = s.get(key, {}); at = cue_frac(s, blk.get("cue"), 0.05 + side * 0.45)
        p = ck.ap(at, 0.4)
        if p <= 0: continue
        col = names[2 + side]; x0 = VX0 + 40 + side * ((VX1 - VX0) / 2 + 20)
        b = (x0, VY0 + 10 + (1 - ease(p)) * 30, x0 + (VX1 - VX0) / 2 - 60, VY1 + 10 + (1 - ease(p)) * 30)
        card(img, b, p, col=mix(T().card, col, 0.12), border=col)
        circle(img, b[0] + 74, b[1] + 74, 38, fill=col, alpha=p)
        paste_rgba(img, icon(names[4 + side], 42, WHITE), b[0] + 53, b[1] + 53, p)
        text(d, (b[0] + 130, b[1] + 74), blk.get("title") or names[side], fk(48), A(col, 255 * p), "lm")
        y = b[1] + 170
        for j, pt in enumerate(blk.get("points", [])):
            q = ck.ap(at + 0.05 + j * 0.06, 0.3)
            for ln in wrap(txt(pt), fs(38), b[2] - b[0] - 100):
                text(d, (b[0] + 60, y), ln, fs(38), A(T().text, 255 * q), "lm"); y += 50
            y += 18

# ------------------------------------------------------------------ recap / task / next
def t_recap(img, d, ck, s, ctx):
    items = s.get("items", []); at = item_times(s, items, 0.08, 0.75)
    text(d, (VCX, VY0 + 10), s.get("title", "RECAP"), fk(54), T().accent, "mm")
    rh = min(150, (VY1 - VY0 - 60) / max(1, len(items)))
    for k, it in enumerate(items):
        p = ck.ap(at[k], 0.35)
        if p <= 0: continue
        y = VY0 + 80 + k * rh + (1 - ease(p)) * 18
        b = (VX0 + 160, y, VX1 - 160, y + rh - 24); card(img, b, p)
        circle(img, b[0] + 70, (b[1] + b[3]) / 2, 40, fill=T().accent, alpha=p)
        text(d, (b[0] + 70, (b[1] + b[3]) / 2), str(k + 1), fk(44), A(T().accent_ink, 255 * p), "mm")
        st = txt(it); text(d, (b[0] + 140, (b[1] + b[3]) / 2), st, fit(st, "InterDisplay-ExtraBold.otf", 52, b[2] - b[0] - 180), A(T().text, 255 * p), "lm")

def t_task(img, d, ck, s, ctx):
    steps = s.get("steps", []); at = item_times(s, steps, 0.1, 0.7)
    b = (VX0 + 120, VY0 - 10, VX1 - 120, VY1 + 20); card(img, b, 1.0, border=T().accent)
    paste_rgba(img, icon("clock", 46, T().accent), b[0] + 40, b[1] + 30)
    text(d, (b[0] + 104, b[1] + 54), s.get("title", f"YOUR {s.get('minutes', 10)}-MINUTE TASK"), fk(42), T().accent, "lm")
    rh = min(100, (b[3] - b[1] - 140) / max(1, len(steps)))
    for k, st in enumerate(steps):
        p = ck.ap(at[k], 0.35)
        if p <= 0: continue
        y = b[1] + 150 + k * rh; cb = (b[0] + 60, y - 28, b[0] + 116, y + 28); done = ck.f > at[k] + 0.12
        rr(img, cb, 12, fill=GREEN if done else None, outline=None if done else T().text, width=4, alpha=p)
        if done: paste_rgba(img, icon("check", 44, WHITE), cb[0] + 6, cb[1] + 6, p)
        text(d, (b[0] + 150, y), txt(st), fit(txt(st), "Inter-SemiBold.otf", 44, b[2] - b[0] - 200), A(T().text, 255 * p), "lm")

def t_next(img, d, ck, s, ctx):
    p = ck.ap(0.0, 0.5)
    text(d, (VCX, VY0 + 80), s.get("label", "NEXT VIDEO"), fb(40), A(T().accent, 255 * p), "mm")
    t_ = s.get("title", ""); text(d, (VCX, VY0 + 220), t_, fit(t_, "InterDisplay-Black.otf", 92, 1600), A(T().text, 255 * p), "mm")
    q = ck.ap(0.25, 0.5); paste_rgba(img, icon("play", 90, T().accent), VCX - 45, VY0 + 340, q)

# ------------------------------------------------------------------ image / screenshot with zoom and callouts
_IMG = {}
def t_image(img, d, ck, s, ctx):
    path = os.path.join(ctx["dir"], s["file"])
    if path not in _IMG: _IMG[path] = Image.open(path).convert("RGB")
    src = _IMG[path]; iw, ih = src.size
    frame = (VX0 - 20, VY0 - 20, VX1 + 20, VY1 + 40) if not s.get("full") else (0, 0, W, H)
    fw, fh = frame[2] - frame[0], frame[3] - frame[1]
    base = min(fw / iw, fh / ih)
    z = s.get("zoom")
    if z:
        zt = float(z["at"]) if "at" in z else cue_frac(s, z.get("cue"), 0.35); zp = easeio(clamp((ck.f - zt) / 0.12))
        zx0, zy0, zx1, zy1 = z["box"]; sc_z = min(fw / (zx1 - zx0), fh / (zy1 - zy0))
        sc = lerp(base, sc_z, zp); cxi = lerp(iw / 2, (zx0 + zx1) / 2, zp); cyi = lerp(ih / 2, (zy0 + zy1) / 2, zp)
    else:
        sc = base * (1 + 0.04 * ck.f); cxi, cyi = iw / 2, ih / 2
    vw, vh = fw / sc, fh / sc
    x0 = clamp(cxi - vw / 2, 0, iw - vw) if vw < iw else cxi - vw / 2
    y0 = clamp(cyi - vh / 2, 0, ih - vh) if vh < ih else cyi - vh / 2
    # visible part of the image, pasted where it falls inside the frame (no black bars from cropping outside)
    ix0, iy0, ix1, iy1 = max(0, x0), max(0, y0), min(iw, x0 + vw), min(ih, y0 + vh)
    px, py = frame[0] + (ix0 - x0) * sc, frame[1] + (iy0 - y0) * sc
    pw, ph = int(round((ix1 - ix0) * sc)), int(round((iy1 - iy0) * sc))
    crop = src.crop((int(ix0), int(iy0), int(ix1), int(iy1))).resize((max(1, pw), max(1, ph)), Image.BICUBIC)
    rad = 0 if s.get("full") else 16
    m = Image.new("L", crop.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, crop.width - 1, crop.height - 1], rad, fill=255)
    if not s.get("full"): rr(img, (px + 6, py + 12, px + pw + 6, py + ph + 16), 18, fill=(0, 0, 0, 110))
    img.paste(crop, (int(px), int(py)), m)
    if not s.get("full"): rr(img, (px - 2, py - 2, px + pw + 2, py + ph + 2), 18, outline=D.T.line, width=2)
    def to_screen(bx):
        return (frame[0] + (bx[0] - x0) * sc, frame[1] + (bx[1] - y0) * sc, frame[0] + (bx[2] - x0) * sc, frame[1] + (bx[3] - y0) * sc)
    for k, hl in enumerate(s.get("highlights", [])):
        t0 = cue_frac(s, hl.get("cue"), 0.3 + k * 0.2); q = clamp((ck.f - t0) / 0.06)
        if q <= 0: continue
        sb = to_screen(hl["box"]); glow(img, sb, 12, col=T().accent, alpha=q, pulse=0.5 + 0.5 * math.sin(ck.t * 5))
        if hl.get("label"):
            cy_ = sb[1] - 50 if sb[1] > frame[1] + 90 else sb[3] + 50
            chip(img, d, clamp((sb[0] + sb[2]) / 2, 300, W - 300), cy_, hl["label"], fb(30), alpha=q)
    if s.get("caption"): chip(img, d, VCX, VY1 + 10, s["caption"], fb(30), WHITE, (0, 0, 0, 200))

# ------------------------------------------------------------------ Claude chat: a prompt types itself, parts get labels, a reply and files appear
CL_BG = (250, 249, 245); CL_TEXT = (40, 38, 34); CL_ACC = (201, 100, 66)
def t_claude(img, d, ck, s, ctx):
    b = (VX0 - 10, VY0 - 20, VX1 + 10, VY1 + 40)
    rr(img, (b[0] + 6, b[1] + 14, b[2] + 6, b[3] + 18), 22, fill=(0, 0, 0, 110)); rr(img, b, 18, fill=CL_BG)
    paste_rgba(img, icon("claude", 40, CL_ACC), b[0] + 40, b[1] + 26); text(d, (b[0] + 94, b[1] + 46), "Claude", fb(32), CL_TEXT, "lm")
    prompt = s.get("prompt", ""); f = fs(int(s.get("size", 38)))
    t0, t1 = s.get("type_at", 0.02), s.get("type_end", 0.35)
    k = clamp((ck.f - t0) / max(0.01, t1 - t0))
    LH = int(f.size * 1.9)
    ib = (b[0] + 60, b[1] + 90, b[2] - 60, b[1] + 90 + 40 + LH * len(wrap(prompt, f, b[2] - b[0] - 200)))
    rr(img, ib, 22, fill=WHITE); rr(img, ib, 22, outline=(214, 210, 200), width=2)
    lines = wrap(prompt, f, ib[2] - ib[0] - 80); pos = []; y = ib[1] + 20 + LH * 0.62; idx = 0
    for ln in lines: pos.append((ln, idx, y)); idx += len(ln) + 1; y += LH
    legend = []
    for mi, m in enumerate(s.get("marks", [])):
        at = m["at"] if "at" in m else cue_frac(s, m.get("cue"), 0.5); q = clamp((ck.f - at) / 0.08)
        st = prompt.find(m["text"])
        if q <= 0 or st < 0: continue
        first = None
        for ln, i0, yy in pos:
            a0, a1 = max(st, i0), min(st + len(m["text"]), i0 + len(ln))
            if a0 < a1:
                x0 = ib[0] + 40 + tw(f, ln[:a0 - i0]); x1 = ib[0] + 40 + tw(f, ln[:a1 - i0])
                rr(img, (x0 - 5, yy - f.size * 0.7, x0 - 5 + (x1 - x0 + 10) * ease(q), yy + f.size * 0.7), 8, fill=(255, 226, 150), alpha=q)
                first = first or (x0, yy)
        legend.append((mi + 1, m.get("label", ""), q, first))
    shown = int(len(prompt) * k); rem = shown
    for ln, i0, yy in pos:
        text(d, (ib[0] + 40, yy), ln[:max(0, rem)], f, CL_TEXT, "lm"); rem -= len(ln) + 1
    for num, lab, q, first in legend:
        if first:
            circle(img, first[0] - 6, first[1] - f.size * 0.72, 15, fill=T().accent, alpha=q)
            text(d, (first[0] - 6, first[1] - f.size * 0.72), str(num), fb(18), A(T().accent_ink, 255 * q), "mm")
    lx, ly = ib[0], ib[3] + 46
    for num, lab, q, first in legend:
        if not lab: continue
        f2 = fb(28); w_ = tw(f2, lab) + 86
        if lx + w_ > ib[2]: lx = ib[0]; ly += 66
        rr(img, (lx, ly - 26, lx + w_, ly + 26), 26, fill=(240, 236, 226), alpha=q)
        circle(img, lx + 28, ly, 17, fill=T().accent, alpha=q); text(d, (lx + 28, ly), str(num), fb(20), A(T().accent_ink, 255 * q), "mm")
        text(d, (lx + 56, ly), lab, f2, A(CL_TEXT, 255 * q), "lm"); lx += w_ + 16
    if legend: ib = (ib[0], ib[1], ib[2], ly + 10)
    if k < 1 and int(ck.t * 2) % 2 == 0:
        last = [p_ for p_ in pos if p_[1] <= shown][-1] if pos else ("", 0, ib[1] + 44)
        cx = ib[0] + 40 + tw(f, prompt[last[1]:shown]) + 3; d.line([(cx, last[2] - f.size * 0.6), (cx, last[2] + f.size * 0.6)], fill=CL_TEXT, width=3)
    y = ib[3] + 40
    if s.get("reply"):
        ra = s.get("reply_at", 0.45); r = clamp((ck.f - ra) / 0.3)
        if r > 0:
            paste_rgba(img, icon("claude", 30, CL_ACC), b[0] + 64, y)
            rl = wrap(s["reply"], fs(30), b[2] - b[0] - 220); n = int(sum(len(l) for l in rl) * r)
            for j, ln in enumerate(rl):
                text(d, (b[0] + 116, y + 16 + j * 42), ln[:max(0, n)], fs(30), CL_TEXT, "lm"); n -= len(ln)
            y += 30 + 42 * len(rl)
    for j, fl in enumerate(s.get("files", [])):
        at = fl.get("at", 0.8) if isinstance(fl, dict) else 0.8
        q = clamp((ck.f - (fl.get("at") if isinstance(fl, dict) and "at" in fl else cue_frac(s, fl.get("cue") if isinstance(fl, dict) else None, at))) / 0.1)
        if q <= 0: continue
        name = txt(fl, "name"); fx_ = b[0] + 64 + j * 520
        rr(img, (fx_, y + 10, fx_ + 490, y + 110), 16, fill=(238, 236, 228), alpha=q)
        rr(img, (fx_ + 18, y + 26, fx_ + 86, y + 94), 12, fill=CL_ACC, alpha=q)
        paste_rgba(img, icon("video" if name.endswith(".mp4") else "file", 40, WHITE), fx_ + 32, y + 40, q)
        text(d, (fx_ + 106, y + 48), name, fit(name, "Inter-SemiBold.otf", 28, 360), A(CL_TEXT, 255 * q), "lm")
        text(d, (fx_ + 106, y + 82), fl.get("meta", "") if isinstance(fl, dict) else "", fs(22), A(UI_MUTED, 255 * q), "lm")

TYPES = {k[2:]: v for k, v in globals().items() if k.startswith("t_")}
