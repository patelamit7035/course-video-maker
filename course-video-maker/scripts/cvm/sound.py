"""Sound for course videos: sound-effect library, a calm teaching music bed, and the voice-first mix."""
import math, os, subprocess, wave
import numpy as np

SR = 48000
_r = np.random.default_rng(11)

def _lp(x, k):
    return np.convolve(x, np.ones(k) / k, mode="same") if k > 1 else x

def _biquad_bp(x, f0s, q=2.0):
    """Band-pass with a time-varying centre frequency (array f0s, same length as x)."""
    y = np.zeros_like(x); x1 = x2 = y1 = y2 = 0.0
    for i in range(len(x)):
        w0 = 2 * math.pi * f0s[i] / SR; al = math.sin(w0) / (2 * q); c = math.cos(w0)
        b0, b2, a0, a1, a2 = al, -al, 1 + al, -2 * c, 1 - al
        yi = (b0 * x[i] + b2 * x2 - a1 * y1 - a2 * y2) / a0
        x2, x1, y2, y1 = x1, x[i], y1, yi; y[i] = yi
    return y

def _env(m, a, d):
    t = np.arange(m) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) * d)

def _write(path, st):
    st = np.clip(st, -1, 1)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((st * 32767).astype(np.int16).tobytes())

# ------------------------------------------------------------------ SFX library
def sfx_whoosh(d=0.38, up=True):
    m = int(d * SR); x = _r.normal(0, 1, m)
    f = np.linspace(400, 4500, m) if up else np.linspace(4500, 400, m)
    y = _biquad_bp(x, f, 1.4) * np.sin(np.linspace(0, math.pi, m)) ** 1.5
    return y / (np.max(np.abs(y)) + 1e-9) * 0.8
def sfx_impact():
    m = int(0.7 * SR); t = np.arange(m) / SR
    sub = np.sin(2 * math.pi * (40 + 70 * np.exp(-t * 14)) * t) * np.exp(-t * 5)
    crack = _lp(_r.normal(0, 1, m), 3) * np.exp(-t * 35)
    return (sub * 0.95 + crack * 0.35)
def sfx_stamp():
    m = int(0.35 * SR); t = np.arange(m) / SR
    return (np.sin(2 * math.pi * (90 + 120 * np.exp(-t * 40)) * t) * np.exp(-t * 18) + _r.normal(0, 1, m) * np.exp(-t * 60) * 0.5) * 0.9
def sfx_pop(f=900):
    m = int(0.1 * SR); t = np.arange(m) / SR
    return np.sin(2 * math.pi * f * (1 + 0.6 * np.exp(-t * 60)) * t) * np.exp(-t * 40) * 0.75
def sfx_click():
    m = int(0.04 * SR); t = np.arange(m) / SR
    return (np.sin(2 * math.pi * 2400 * t) * np.exp(-t * 160) + _r.normal(0, 1, m) * np.exp(-t * 300) * 0.4) * 0.6
def sfx_ding(f=1320):
    m = int(0.6 * SR); t = np.arange(m) / SR
    y = sum(a * np.sin(2 * math.pi * f * h * t) * np.exp(-t * dcy) for h, a, dcy in ((1, 1, 6), (2.0, 0.45, 9), (3.01, 0.25, 12), (4.2, 0.12, 16)))
    return y * 0.32
def sfx_notify():
    return np.concatenate([sfx_ding(1047)[: int(0.12 * SR)], sfx_ding(1568)]) * 0.9
def sfx_type(n=6, gap=0.07):
    out = np.zeros(int((n * gap + 0.05) * SR))
    for k in range(n):
        c = sfx_click() * (0.5 + 0.3 * _r.random()); i = int(k * gap * SR); out[i:i + len(c)] += c[: len(out) - i]
    return out
def sfx_riser(d=0.9):
    m = int(d * SR); t = np.arange(m) / SR
    tone = np.sin(2 * math.pi * (250 * t + 700 * t ** 2 / d)) * 0.5
    noise = _biquad_bp(_r.normal(0, 1, m), np.linspace(800, 6000, m), 1.0) * 0.4
    return (tone + noise / (np.max(np.abs(noise)) + 1e-9) * 0.5) * (t / d) ** 2 * 0.6
def sfx_drop(d=0.9):
    m = int(d * SR); t = np.arange(m) / SR
    return np.sin(2 * math.pi * (300 * t - 120 * t ** 2 / d)) * np.exp(-t * 2.5) * 0.5
def sfx_tick():
    m = int(0.025 * SR); return _r.normal(0, 1, m) * np.exp(-np.arange(m) / SR * 250) * 0.45
def sfx_shimmer(d=0.7):
    m = int(d * SR); t = np.arange(m) / SR
    y = sum(np.sin(2 * math.pi * f * t + p) for f, p in ((2093, 0), (2637, 1), (3136, 2), (4186, 3)))
    return y * np.sin(np.linspace(0, math.pi, m)) * 0.09
def sfx_flip():
    return np.concatenate([sfx_whoosh(0.18, True) * 0.7, sfx_click()])

SFX = dict(whoosh=sfx_whoosh, impact=sfx_impact, stamp=sfx_stamp, pop=sfx_pop, click=sfx_click, ding=sfx_ding,
           notify=sfx_notify, type=sfx_type, riser=sfx_riser, drop=sfx_drop, tick=sfx_tick, shimmer=sfx_shimmer, flip=sfx_flip)

def render_sfx(total, events):
    n = int(total * SR); st = np.zeros((n, 2))
    for ev in events:
        name, at = ev[0], ev[1]; g = ev[2] if len(ev) > 2 else 0.7; arg = ev[3] if len(ev) > 3 else None
        sig = SFX[name](arg) if arg is not None else SFX[name]()
        i = int(at * SR)
        if i >= n or i < 0: continue
        sig = sig[: n - i]; pan = ((hash((name, round(at, 2))) % 7) - 3) * 0.08
        st[i:i + len(sig), 0] += sig * g * (1 - max(0, pan)); st[i:i + len(sig), 1] += sig * g * (1 + min(0, pan))
    return st

def music(total, mood="calm"):
    """Teaching bed: C-G-Am-F pad with soft plucks, 78 BPM, no beat (never fights a teaching voice)."""
    n = int(total * SR); out = np.zeros((n, 2))
    chords = [(130.81, 164.81, 196.0, 261.63), (98.0, 123.47, 146.83, 196.0), (110.0, 130.81, 164.81, 220.0), (87.31, 110.0, 130.81, 174.61)]
    bar = 4 * 60 / (78 if mood == "calm" else 96)
    for b in range(int(total / bar) + 1):
        t0 = b * bar
        if t0 >= total: break
        m = min(int(bar * 1.15 * SR), n - int(t0 * SR)); tt = np.arange(m) / SR
        env = np.minimum(1, tt / 0.8) * np.minimum(1, np.maximum(0, (bar * 1.15 - tt)) / 0.6)
        ch = chords[b % 4]
        sig = sum(np.sin(2 * np.pi * f * tt) * 0.5 + 0.25 * np.sin(2 * np.pi * f * 2.003 * tt) for f in ch) * env * 0.05
        i0 = int(t0 * SR); out[i0:i0 + m, 0] += sig; out[i0:i0 + m, 1] += np.roll(sig, 200)
        for k in range(8):
            ts = t0 + k * bar / 8
            if ts >= total: break
            f = ch[[0, 2, 1, 3, 2, 1, 3, 2][k]] * 2
            mm = min(int(0.6 * SR), n - int(ts * SR)); ttt = np.arange(mm) / SR
            pl = np.sin(2 * np.pi * f * ttt) * np.exp(-ttt * 6) * 0.035
            j = int(ts * SR); pan = 0.3 if k % 2 else -0.3
            out[j:j + mm, 0] += pl * (1 - pan); out[j:j + mm, 1] += pl * (1 + pan)
    fade = np.minimum(1, np.arange(n) / SR / 1.5) * np.minimum(1, (total - np.arange(n) / SR) / 2.0)
    return out * fade[:, None]

def _wav(path, st):
    st = np.clip(st, -1, 1)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((st * 32767).astype(np.int16).tobytes())

def mix(total, voice_segments, events, out_wav, music_on=True, music_level=0.32):
    """voice_segments: [(start_sec, mono float32 array at SR)]. The sound is built 4 s longer than the picture
    because loudnorm's look-ahead swallows the last ~3 s; the final mux cuts it to the picture."""
    T = total + 4.0; n = int(T * SR)
    voice = np.zeros(n)
    for at, seg in voice_segments:
        seg = seg.copy(); fl = min(len(seg) // 2, int(0.03 * SR))
        if fl: seg[:fl] *= np.linspace(0, 1, fl); seg[-fl:] *= np.linspace(1, 0, fl)
        i = int(at * SR); seg = seg[: max(0, n - i)]; voice[i:i + len(seg)] += seg
    m = music(T) if music_on else np.zeros((n, 2)); m = m / (np.max(np.abs(m)) + 1e-9) * 0.6
    fx = render_sfx(T, events); fx = fx / (np.max(np.abs(fx)) + 1e-9) * 0.7
    d = os.path.dirname(os.path.abspath(out_wav))
    vp, mp, fp = os.path.join(d, "_v.wav"), os.path.join(d, "_m.wav"), os.path.join(d, "_f.wav")
    _wav(vp, np.stack([voice, voice], 1)); _wav(mp, m); _wav(fp, fx)
    has_voice = bool(voice_segments)
    if has_voice:
        graph = ("[0:a]volume=0.7,highpass=f=80,acompressor=threshold=0.08:ratio=3:attack=6:release=120:makeup=2,loudnorm=I=-16:TP=-2:LRA=7,asplit=2[v][k];"
                 f"[1:a]volume={music_level}[mr];[mr][k]sidechaincompress=threshold=0.04:ratio=5:attack=40:release=500[md];"
                 "[2:a]volume=0.45[fx];[v][md][fx]amix=inputs=3:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=9,"
                 "aresample=192000,alimiter=limit=0.66:attack=1:release=50:level=false,aresample=48000[a]")
    else:
        graph = "[1:a]volume=0.55[mr];[2:a]volume=0.6[fx];[mr][fx]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-20:TP=-2:LRA=9[a]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vp, "-i", mp, "-i", fp, "-filter_complex", graph, "-map", "[a]",
                    "-ar", str(SR), "-ac", "2", out_wav], check=True)
    for p in (vp, mp, fp): os.remove(p)
