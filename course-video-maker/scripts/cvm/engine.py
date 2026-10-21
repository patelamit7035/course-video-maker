"""Timeline, frames, avatar cuts, watermark, captions, chunked rendering and the final MP4."""
import json, math, os, re, subprocess, sys, time
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from core import *
import draw as D
import scenes as TY
import sound as SND
import voice as VO

LEAD, TAIL, WPS, MIN_SCENE = 0.45, 0.35, 2.5, 3.0
POP_LEN, POP_FADE, POP_GAP = 1.5, 0.18, 20.0
VSR = 24000

# ------------------------------------------------------------------ project
def load(path):
    pj = json.load(open(path))
    pj["_dir"] = os.path.dirname(os.path.abspath(path))
    pj.setdefault("voice", {"mode": "none"}); pj.setdefault("captions", True); pj.setdefault("music", True)
    brand = dict(pj.get("brand", {})); brand.setdefault("course", pj.get("course", ""))
    D.T = D.Theme(brand)
    for k, s in enumerate(pj["scenes"]):
        if s.get("type") not in TY.TYPES: raise SystemExit(f"Scene {k + 1}: unknown type '{s.get('type')}'. Types: {', '.join(sorted(TY.TYPES))}")
        if not s.get("vo"): raise SystemExit(f"Scene {k + 1}: 'vo' (the voiceover line) is empty")
    return pj

def work_dir(pj):
    w = os.path.join(pj["_dir"], "work", re.sub(r"[^a-z0-9]+", "_", pj.get("title", "video").lower()).strip("_"))
    os.makedirs(w, exist_ok=True); return w

# ------------------------------------------------------------------ voice + timeline
def voice_clips(pj, log=print):
    mode = pj["voice"].get("mode", "none")
    if mode == "gemini": return VO.gemini_scenes(pj, pj["_dir"], os.path.join(work_dir(pj), "voice"), log)
    if mode == "file": return VO.file_scenes(pj, pj["_dir"])
    return None

def timeline(pj, clips):
    t = 0.0; sc = []
    for i, s in enumerate(pj["scenes"]):
        vlen = len(clips[i]) / VSR if clips is not None else len(s["vo"].split()) / WPS
        dur = max(MIN_SCENE, LEAD + vlen + float(s.get("hold", 0.6)) + TAIL)
        subs = chunks(s.get("caption", s["vo"]))
        lens = np.array([len(c) + 6 for c in subs], float); acc = np.concatenate([[0], np.cumsum(lens)]) / lens.sum() * vlen
        sc.append(dict(i=i, t0=t, dur=dur, vstart=t + LEAD, vlen=vlen, s=s,
                       subs=[(t + LEAD + acc[k], t + LEAD + acc[k + 1], c) for k, c in enumerate(subs)]))
        t += dur
    tl = dict(pj=pj, scenes=sc, total=t)
    tl["pops"] = pops(tl)
    return tl

def chunks(s, maxw=8, maxc=52):
    words = s.split(); out, cur = [], []
    for w_ in words:
        cur.append(w_); txt_ = " ".join(cur)
        if (w_[-1] in ".?!:" and len(cur) >= 3) or (w_[-1] == "," and len(cur) >= 5) or len(cur) >= maxw or len(txt_) >= maxc:
            out.append(txt_); cur = []
    if cur:
        if out and len(cur) <= 2 and len(out[-1]) + len(" ".join(cur)) < 64: out[-1] += " " + " ".join(cur)
        else: out.append(" ".join(cur))
    return out or [""]

# ------------------------------------------------------------------ avatar cuts (1.5 s, never closer than 20 s)
def pops(tl):
    av = tl["pj"].get("avatar")
    if not av: return []
    out, last = [], -1e9
    for sc in tl["scenes"]:
        mode = sc["s"].get("avatar")
        if mode not in ("full", "bubble"): continue
        t = sc["t0"] + 0.05
        if t - last < POP_GAP: print(f"  note: avatar in scene {sc['i'] + 1} skipped (less than {POP_GAP:.0f} s after the last one)"); continue
        out.append((t, mode, len(out))); last = t
    return out

def prepare_avatar(tl):
    """Frames for each cut: from the student's clips (rotating) or a still photo with a slow zoom."""
    av = tl["pj"].get("avatar"); w = os.path.join(work_dir(tl["pj"]), "avatar")
    if not av or not tl["pops"]: return
    os.makedirs(w, exist_ok=True)
    clips = [os.path.join(tl["pj"]["_dir"], c) for c in av.get("clips", [])]
    for t0, mode, i in tl["pops"]:
        dst = os.path.join(w, f"cut{i}")
        if os.path.exists(os.path.join(dst, "045.jpg")) or os.path.exists(os.path.join(dst, "photo.jpg")): continue
        os.makedirs(dst, exist_ok=True)
        if clips:
            c = clips[i % len(clips)]
            dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", c], capture_output=True, text=True).stdout.strip() or 3)
            start = (i * 1.7) % max(0.1, dur - POP_LEN - 0.2)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.2f}", "-i", c, "-t", f"{POP_LEN + 0.1:.2f}", "-vf",
                            "fps=30,scale=540:960:force_original_aspect_ratio=increase,crop=540:960", "-q:v", "3", os.path.join(dst, "%03d.jpg")], check=True)
        elif av.get("photo"):
            im = Image.open(os.path.join(tl["pj"]["_dir"], av["photo"])).convert("RGB")
            r = max(540 / im.width, 960 / im.height); im = im.resize((int(im.width * r), int(im.height * r)))
            im.crop(((im.width - 540) // 2, (im.height - 960) // 2, (im.width - 540) // 2 + 540, (im.height - 960) // 2 + 960)).save(os.path.join(dst, "photo.jpg"))

_BGC = {}
def draw_pop(img, t, tl):
    w = os.path.join(work_dir(tl["pj"]), "avatar")
    for t0, mode, i in tl["pops"]:
        lt = t - t0
        if not (0 <= lt < POP_LEN): continue
        a = clamp(lt / POP_FADE) * clamp((POP_LEN - lt) / POP_FADE)
        fn = os.path.join(w, f"cut{i}", f"{min(45, int(lt * 30) + 1):03d}.jpg")
        if not os.path.exists(fn): fn = os.path.join(w, f"cut{i}", "photo.jpg")
        if not os.path.exists(fn): return img
        fr = Image.open(fn).convert("RGB"); zoom = 1.0 + 0.05 * lt / POP_LEN
        if mode == "full":
            if i not in _BGC:
                small = fr.resize((96, 170)).crop((0, 30, 96, 84)).resize((W, H)).filter(ImageFilter.GaussianBlur(30))
                _BGC[i] = Image.blend(small, Image.new("RGB", (W, H), (8, 9, 18)), 0.45)
            layer = _BGC[i].copy(); ch = int(900 * zoom); cw = int(ch * 9 / 16)
            fg = fr.resize((cw, ch), Image.LANCZOS)
            m = Image.new("L", (cw, ch), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, cw - 1, ch - 1], 34, fill=255)
            layer.paste(fg, (int(W / 2 - cw / 2), int(H / 2 - ch / 2 + 20)), m)
            rr(layer, (W / 2 - cw / 2 - 4, H / 2 - ch / 2 + 16, W / 2 + cw / 2 + 4, H / 2 + ch / 2 + 24), 36, outline=D.T.accent, width=4)
            img = Image.blend(img, layer, a)
        else:
            r = 130; cx, cy = W - 210, 760
            face = fr.crop((90, 120, 450, 480)).resize((int(2 * r * zoom), int(2 * r * zoom)), Image.LANCZOS)
            o = (face.width - 2 * r) // 2; face = face.crop((o, o, o + 2 * r, o + 2 * r))
            circle(img, cx, cy + 6, r + 10, fill=(0, 0, 0, 140), alpha=a); circle(img, cx, cy, r + 8, fill=D.T.accent, alpha=a)
            m = Image.new("L", (2 * r, 2 * r), 0); ImageDraw.Draw(m).ellipse([0, 0, 2 * r - 1, 2 * r - 1], fill=int(255 * a))
            img.paste(face, (cx - r, cy - r), m)
    return img

# ------------------------------------------------------------------ chrome
_BG = {}
def background():
    if "bg" in _BG: return _BG["bg"]
    th = D.T; im = Image.new("RGB", (W, H), th.bg0); d = ImageDraw.Draw(im, "RGBA")
    for y in range(H):
        k = y / H; d.line([(0, y), (W, y)], fill=mix(th.bg0, th.bg1, k))
    for gx in range(0, W, 80): d.line([(gx, 0), (gx, H)], fill=th.grid)
    for gy in range(0, H, 80): d.line([(0, gy), (W, gy)], fill=th.grid)
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    gd.ellipse([W - 700, -500, W + 400, 450], fill=th.accent + (34,)); gd.ellipse([-500, H - 300, 600, H + 500], fill=(80, 110, 255, 22))
    g = g.filter(ImageFilter.GaussianBlur(120)); im.paste(g, (0, 0), g)
    _BG["bg"] = im; return im

def top_bar(img, d, pj, prog):
    th = D.T; x = 48
    for lab, fg, bg in ((pj.get("module", ""), th.accent_ink, th.accent), (pj.get("lesson", ""), WHITE if not th.light else th.text, th.card2)):
        if not lab: continue
        f = fb(24); h = f.size + 22; w = tw(f, lab) + 36
        rr(img, (x, 52 - h / 2, x + w, 52 + h / 2), h / 2, fill=bg); text(d, (x + 18, 52), lab, f, fg, "lm"); x += w + 14
    text(d, (x + 8, 52), pj.get("title", ""), fs(28), th.text, "lm")
    if th.course: text(d, (W - 48, 52), th.course.upper(), fb(22), th.muted, "rm")
    rr(img, (0, 0, W, 6), 0, fill=th.line); rr(img, (0, 0, W * prog, 6), 0, fill=th.accent)

def headline(img, d, head, ck):
    if not head: return
    q = ck.ap(0.0, 0.4); f = fit(head, "InterDisplay-Black.otf", 64, 1700)
    text(d, (W / 2, 160 + (1 - ease(q)) * 10), head, f, A(D.T.text, 255 * q), "mm")
    wv = tw(f, head); rr(img, (W / 2 - wv / 2, 202, W / 2 - wv / 2 + wv * ease(q), 208), 3, fill=D.T.accent, alpha=q)

WM_SPOTS = [(60, 942, "lm"), (W - 60, 942, "rm")]
def watermark(img, t):
    wm = D.T.watermark
    if not wm: return
    k = int(t // 38.0); lt = t - k * 38.0
    if lt > 11: return
    a = clamp(lt / 2.0) * clamp((11 - lt) / 2.0) * (0.10 if D.T.light else 0.13)
    x, y, anc = WM_SPOTS[k % len(WM_SPOTS)]
    text(ImageDraw.Draw(img, "RGBA"), (x, y), wm, fb(30), A(D.T.text, 255 * a), anc)

def subtitle(img, d, txt, alpha, keys):
    if not txt or alpha <= 0.01: return
    f = fs(36); lines = wrap(txt, f, 1560); lh = 48; h = lh * len(lines) + 26
    wmax = max(tw(f, l) for l in lines) + 60; y0 = 1046 - h
    rr(img, (W / 2 - wmax / 2, y0, W / 2 + wmax / 2, y0 + h), 18, fill=(0, 0, 0, 175), alpha=alpha)
    for k, l in enumerate(lines):
        x = W / 2 - tw(f, l) / 2; y = y0 + 13 + lh / 2 + k * lh
        for part in re.split(r"(\s+)", l):
            if not part: continue
            col = D.T.accent if part.strip(".,?!:").lower() in keys else WHITE
            text(d, (x, y), part, f, A(col, 255 * alpha), "lm"); x += tw(f, part)

# ------------------------------------------------------------------ frames
def frame(tl, t):
    pj = tl["pj"]; sc = tl["scenes"][-1]
    for s in tl["scenes"]:
        if s["t0"] <= t < s["t0"] + s["dur"]: sc = s; break
    lt = t - sc["t0"]
    img = background().copy(); watermark(img, t)
    d = ImageDraw.Draw(img, "RGBA"); top_bar(img, d, pj, t / tl["total"]); base = img.copy()
    ck = Clock(lt - LEAD + 0.25, sc["vlen"] + 0.25); ck.t = max(0.0, ck.t)
    ctx = dict(dir=pj["_dir"], title=pj.get("title", ""))
    s = sc["s"]; TY.TYPES[s["type"]](img, d, ck, s, ctx); headline(img, d, s.get("head", ""), ck)
    last = sc is tl["scenes"][-1]
    fade = min(1.0, lt / 0.3, (sc["dur"] - lt) / 0.25 if not last else 1.0)
    if last: fade = min(fade, (tl["total"] - t) / 0.6)
    if fade < 1.0: img = Image.blend(base, img, max(0.0, fade))
    img = draw_pop(img, t, tl)
    if pj.get("captions", True):
        d = ImageDraw.Draw(img, "RGBA"); keys = {k.lower() for k in pj.get("caption_keywords", [])}
        for a_, b_, c in sc["subs"]:
            if a_ - 0.05 <= t < b_ + 0.15: subtitle(img, d, c, clamp((t - a_ + 0.05) / 0.12) * clamp((b_ + 0.15 - t) / 0.12), keys); break
    return img

# ------------------------------------------------------------------ sound effects from the scenes
def sfx_events(tl):
    ev = []
    for sc in tl["scenes"]:
        s = sc["s"]; t0 = sc["vstart"] - 0.25; L = sc["vlen"] + 0.25; Tm = lambda f: t0 + f * L
        ev.append(("whoosh", max(0.0, sc["t0"] - 0.05), 0.16))
        ty = s["type"]
        wb = ty == "whiteboard"
        for key in ("bullets", "lines", "items", "steps", "messages"):
            if isinstance(s.get(key), list):
                for f in D.item_times(s, s[key], 0.12 if wb else 0.06, 0.75 if wb else 0.78):
                    ev.append(("tick", Tm(f), 0.32) if (wb or key == "steps") else ("pop", Tm(f), 0.3, 880))
        if ty == "quiz": ev.append(("ding", Tm(D.cue_frac(s, s.get("reveal_cue"), 0.75)), 0.35, 1320))
        if ty == "ui":
            for k, c in enumerate(s.get("clicks", [])): ev.append(("click", Tm(D.cue_frac(s, c.get("cue") if isinstance(c, dict) else None, 0.3 + k * 0.25)), 0.5))
        if ty in ("next", "title"): ev.append(("shimmer", sc["t0"] + 0.2, 0.4))
    for t0, mode, _ in tl["pops"]: ev.append(("whoosh", max(0.0, t0 - 0.08), 0.22))
    return ev

# ------------------------------------------------------------------ rendering (in chunks, so a long video survives time limits)
_TL = {}
def _init(path, clips_path):
    pj = load(path); clips = list(np.load(clips_path, allow_pickle=True)) if clips_path else None
    _TL["tl"] = timeline(pj, clips)
def _work(t): return frame(_TL["tl"], t).tobytes()

def _clips_file(pj, clips):
    if clips is None: return None
    p = os.path.join(work_dir(pj), "clips.npy"); np.save(p, np.array(clips, dtype=object), allow_pickle=True); return p

def render(path, budget=None, procs=None, fps=None, crf=21, log=print):
    """Renders scene chunks into work/chunks until done or until the time budget (seconds) is used.
    Returns True when the final MP4 is written, False when it needs to be run again to continue."""
    start = time.time(); pj = load(path); w = work_dir(pj)
    fps = int(fps or pj.get("fps", 30))
    clips = voice_clips(pj, log); tl = timeline(pj, clips); prepare_avatar(tl)
    cp = _clips_file(pj, clips); cdir = os.path.join(w, "chunks"); os.makedirs(cdir, exist_ok=True)
    procs = procs or max(1, min(4, os.cpu_count() or 1))
    sig = json.dumps([[s["s"], round(s["dur"], 3)] for s in tl["scenes"]], sort_keys=True, default=str)
    for sc in tl["scenes"]:
        out = os.path.join(cdir, f"scene{sc['i'] + 1:03d}.mp4"); tag = out + ".sig"
        key = json.dumps([sc["s"], round(sc["dur"], 3), round(sc["t0"], 3), pj.get("brand"), pj.get("title"), [p[:2] for p in tl["pops"]]], sort_keys=True, default=str)
        if os.path.exists(out) and os.path.exists(tag) and open(tag).read() == key: continue
        if budget and time.time() - start > budget:
            log(f"PAUSED: time budget used. Run the same command again to continue (scene {sc['i'] + 1} of {len(tl['scenes'])})."); return False
        n0, n1 = int(round(sc["t0"] * fps)), int(round((sc["t0"] + sc["dur"]) * fps))
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
                                "-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf), "-pix_fmt", "yuv420p", "-tune", "animation", out + ".tmp.mp4"], stdin=subprocess.PIPE)
        times = [k / fps for k in range(n0, n1)]
        if procs > 1:
            with Pool(procs, initializer=_init, initargs=(path, cp)) as pool:
                for buf in pool.imap(_work, times, chunksize=8): enc.stdin.write(buf)
        else:
            _TL["tl"] = tl
            for t in times: enc.stdin.write(_work(t))
        enc.stdin.close(); enc.wait(); os.replace(out + ".tmp.mp4", out); open(tag, "w").write(key)
        log(f"  scene {sc['i'] + 1}/{len(tl['scenes'])} rendered ({n1 - n0} frames)")
    # final: join scenes, build the sound, mux
    lst = os.path.join(w, "chunks.txt")
    open(lst, "w").write("".join(f"file '{os.path.join(cdir, f'scene{k + 1:03d}.mp4')}'\n" for k in range(len(tl["scenes"]))))
    silent = os.path.join(w, "_silent.mp4"); wav = os.path.join(w, "_audio.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent], check=True)
    segs = [(sc["vstart"], clips[sc["i"]]) for sc in tl["scenes"]] if clips is not None else []
    if segs:   # sound module works at 48 kHz
        segs = [(a, np.interp(np.arange(int(len(x) * 2)) / 2, np.arange(len(x)), x).astype(np.float32)) for a, x in segs]
    SND.mix(tl["total"], segs, sfx_events(tl), wav, music_on=pj.get("music", True), music_level=float(pj.get("music_level", 0.32)))
    name = re.sub(r"[^A-Za-z0-9 _-]+", "", pj.get("output", pj.get("title", "video"))).strip() or "video"
    final = os.path.join(pj["_dir"], name + ".mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                    "-shortest", "-movflags", "+faststart", final], check=True)
    os.remove(silent); os.remove(wav)
    size = os.path.getsize(final) / 1e6
    log(f"DONE: {final}  {tl['total']:.1f}s  {size:.1f} MB")
    if size > 29: log("NOTE: file is over the 30 MB chat limit. Run with --crf 26 or split the video into two projects.")
    write_srt(tl, os.path.join(pj["_dir"], name + ".srt"))
    return True

def write_srt(tl, path):
    def ts(x):
        ms = int(round(x * 1000)); return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    k = 1; lines = []
    for sc in tl["scenes"]:
        for a, b, c in sc["subs"]: lines += [str(k), f"{ts(a)} --> {ts(b)}", c, ""]; k += 1
    open(path, "w").write("\n".join(lines))

def preview(path, log=print, with_voice=False):
    """One contact sheet: two stills per scene, to check the look before spending time on the render."""
    pj = load(path); clips = voice_clips(pj, log) if with_voice else None
    tl = timeline(pj, clips); prepare_avatar(tl); ims = []
    for sc in tl["scenes"]:
        for frac in (0.4, 0.95):
            t = sc["vstart"] - 0.25 + frac * (sc["vlen"] + 0.25)
            ims.append(frame(tl, min(t, sc["t0"] + sc["dur"] - 0.3)).resize((640, 360), Image.LANCZOS))
    cols = 4; rows = math.ceil(len(ims) / cols); S = Image.new("RGB", (cols * 640, rows * 360))
    for k, im in enumerate(ims): S.paste(im, ((k % cols) * 640, (k // cols) * 360))
    out = os.path.join(pj["_dir"], "preview.png"); S.save(out)
    log(f"PREVIEW: {out}  ({len(tl['scenes'])} scenes, about {tl['total']:.0f}s)"); return out

def still(path, scene, frac=0.6):
    pj = load(path); tl = timeline(pj, None); prepare_avatar(tl); sc = tl["scenes"][scene - 1]
    t = sc["vstart"] - 0.25 + frac * (sc["vlen"] + 0.25); out = os.path.join(pj["_dir"], f"still_scene{scene}.png")
    frame(tl, t).save(out); return out
