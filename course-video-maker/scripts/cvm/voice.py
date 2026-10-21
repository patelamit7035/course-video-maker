"""Voiceover for course videos.

Three ways, chosen in project.json -> "voice":
  {"mode": "gemini", "voice_id": "voice_xxxx"}   Gemini text-to-speech with the student's cloned (replicated) voice,
                                                  or a ready voice name such as "Charon" / "Kore"
  {"mode": "file", "file": "my_recording.mp3"}   the student's own recording: one file, scenes read in order with a
                                                  1 to 2 second pause between scenes
  {"mode": "none"}                                no voice: scenes are timed at a natural speaking pace

The Gemini key is read from the environment (GEMINI_API_KEY) or from a file named in GEMINI_KEY_FILE, or from
gemini_key.txt next to project.json. It is never printed.
"""
import base64, hashlib, io, json, os, re, subprocess, time, urllib.error, urllib.request, wave
import numpy as np

SR = 24000
MODEL = os.environ.get("GEMINI_TTS_MODEL", "gemini-3.8-flash-tts")
API = "https://generativelanguage.googleapis.com/v1beta"
STYLE = "Calm, warm teacher explaining to a beginner. Clear words, friendly, unhurried, natural pace."

def gemini_key(project_dir=None):
    k = os.environ.get("GEMINI_API_KEY")
    if k: return k.strip()
    p = os.environ.get("GEMINI_KEY_FILE")
    if p and os.path.exists(p): return open(p).read().strip()
    if project_dir:
        p = os.path.join(project_dir, "gemini_key.txt")
        if os.path.exists(p): return open(p).read().strip()
    raise SystemExit("No Gemini key: set GEMINI_API_KEY, or put the key in gemini_key.txt next to project.json")

def _req(method, url, key, body=None, timeout=180):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data, {"Content-Type": "application/json", "x-goog-api-key": key}, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r: return json.load(r)

def _pcm(b):
    if b[:4] == b"RIFF":
        with wave.open(io.BytesIO(b)) as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16)
    return np.frombuffer(b, np.int16)

def tts(text, voice, key, style=STYLE):
    """One clip of speech (int16, 24 kHz). voice = a replicated voice id (voice_...) or a ready voice name."""
    global MODEL
    part = {"text": text}
    if style: part["speech_metadata"] = {"style": style}
    vc = {"voice": voice} if voice.startswith(("voice_", "voicekey_")) else {"prebuiltVoiceConfig": {"voiceName": voice}}
    body = {"contents": [{"role": "user", "parts": [part]}],
            "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": vc}}}
    for attempt in range(5):
        try:
            data = _req("POST", f"{API}/models/{MODEL}:generateContent", key, body)
            try: return _pcm(base64.b64decode(data["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]))
            except (KeyError, IndexError): time.sleep(4); continue
        except urllib.error.HTTPError as e:
            full = e.read().decode(errors="replace"); msg = full[:600]
            if re.search(r'quotaId"\s*:\s*"[^"]*PerDay', full): msg = "PerDay " + msg   # only a real daily-quota violation
            if e.code == 400 and style and ("speech_metadata" in msg or "speech metadata" in msg.lower()): return tts(text, voice, key, style=None)
            if e.code == 429 and msg.startswith("PerDay"):
                if MODEL != "gemini-3.8-flash-lite-tts" and voice.startswith("voice_"):
                    MODEL = "gemini-3.8-flash-lite-tts"; print("  daily limit reached: switching to gemini-3.8-flash-lite-tts (same voice)"); continue
                raise SystemExit("Gemini voice daily limit used up. Try again tomorrow, or use a paid key.")
            if e.code in (429, 500, 503) and attempt < 4: time.sleep(20 * (attempt + 1)); continue
            raise SystemExit(f"Gemini voice error {e.code}: {msg}")
        except urllib.error.URLError as e:
            raise SystemExit("Cannot reach Gemini (generativelanguage.googleapis.com). In Claude: Settings > Capabilities, "
                             f"turn on network access (Allow network egress). Details: {e.reason}")
    raise SystemExit("Gemini voice gave no audio after 5 tries")

def _trim(x, thr=300):
    idx = np.where(np.abs(x) > thr)[0]
    return x[max(0, idx[0] - 1200): idx[-1] + 2400] if len(idx) else x

PAUSE = "\n\n[long pause]\n\n"

def _runs(x, thr=300, min_len=0.25):
    """Silent stretches (start, length) in seconds, plus where speech starts and ends."""
    win = int(0.02 * SR); n = len(x) // win
    e = np.sqrt((x[:n * win].astype(np.float64).reshape(n, win) ** 2).mean(1))
    voiced = np.where(e >= thr)[0]
    if not len(voiced): return [], 0, len(x) / SR
    s0, s1 = voiced[0] * 0.02, (voiced[-1] + 1) * 0.02
    out = []; i = voiced[0]
    while i <= voiced[-1]:
        if e[i] < thr:
            j = i
            while j < n and e[j] < thr: j += 1
            if (j - i) * 0.02 >= min_len: out.append((i * 0.02, (j - i) * 0.02))
            i = j
        else: i += 1
    return out, s0, s1

def split_batch(x, texts):
    """Cut one clip that reads several scenes (joined with long pauses) back into one clip per scene.
    Picks the pauses that best match where the text says each break is; returns None when unsure."""
    runs, s0, s1 = _runs(x)
    n = len(texts); D = s1 - s0
    if len(runs) < n - 1 or D <= 0: return None
    lens = np.array([max(1, len(t)) for t in texts], float)
    exp = s0 + np.cumsum(lens)[:-1] / lens.sum() * D
    tol = max(3.0, 0.15 * D)
    mids = [r[0] + r[1] / 2 for r in runs]
    NEG = -1e9; R = len(runs)
    best = [[NEG] * R for _ in range(n - 1)]; back = [[-1] * R for _ in range(n - 1)]
    for j in range(n - 1):
        for k in range(R):
            dev = abs(mids[k] - exp[j])
            if dev > tol: continue
            sc = runs[k][1] - 0.35 * dev
            if j == 0: best[j][k] = sc
            else:
                prev = max(range(k), key=lambda q: best[j - 1][q], default=None)
                if prev is None or best[j - 1][prev] <= NEG / 2: continue
                best[j][k] = best[j - 1][prev] + sc; back[j][k] = prev
    k = max(range(R), key=lambda q: best[n - 2][q])
    if best[n - 2][k] <= NEG / 2: return None
    picks = [k]
    for j in range(n - 2, 0, -1): k = back[j][k]; picks.append(k)
    picks = picks[::-1]
    if min(runs[k][1] for k in picks) < 0.3: return None
    bounds = [s0] + [mids[k] for k in picks] + [s1]
    durs = np.diff(bounds); rate = durs / lens; m = durs.sum() / lens.sum()
    if (rate < 0.6 * m).any() or (rate > 1.6 * m).any(): return None
    cps = lens / durs                    # characters per second: Hinglish speech is about 11 to 14
    if not (9.0 <= lens.sum() / D <= 17.0) or (cps > 20).any() or (cps < 6.5).any(): return None   # text was skipped or stretched
    return [_trim(x[int(a * SR):int(b * SR)]) for a, b in zip(bounds, bounds[1:])]

def gemini_scenes(project, project_dir, cache_dir, log=print):
    """Speech for every scene, cached per scene text (changing one line re-voices only that scene).
    voice.batch (or GEMINI_TTS_BATCH) > 1 reads several scenes per request and cuts them apart: fewer requests
    when the daily limit is small. Groups that cannot be cut safely are read again in smaller groups."""
    key = gemini_key(project_dir); voice = project["voice"].get("voice_id") or project["voice"].get("name", "Charon")
    batch = int(project["voice"].get("batch") or os.environ.get("GEMINI_TTS_BATCH") or 1)
    os.makedirs(cache_dir, exist_ok=True); N = len(project["scenes"])
    paths = []
    for k, s in enumerate(project["scenes"]):
        h = hashlib.sha1((s["vo"] + "|" + voice).encode()).hexdigest()[:10]
        paths.append(os.path.join(cache_dir, f"s{k + 1:02d}_{h}.npy"))
    missing = [k for k in range(N) if not os.path.exists(paths[k])]

    def single(k):
        vo = project["scenes"][k]["vo"]; need = max(len(vo.split()) / 4.0, len(vo) / 19.0)
        for tries in range(3):
            x = _trim(tts(project["scenes"][k]["vo"], voice, key))
            if len(x) / SR >= need or tries == 2: break
        np.save(paths[k], x); log(f"  voice scene {k + 1}/{N}: {len(x) / SR:.1f}s")

    def group(ks):
        if len(ks) == 1: return single(ks[0])
        texts = [project["scenes"][k]["vo"] for k in ks]
        parts = split_batch(tts(PAUSE.join(texts), voice, key), texts)
        if parts is None:
            log(f"  voice scenes {ks[0] + 1}-{ks[-1] + 1}: could not cut safely, reading in smaller groups")
            h = len(ks) // 2; group(ks[:h]); group(ks[h:]); return
        for k, x in zip(ks, parts):
            np.save(paths[k], x); log(f"  voice scene {k + 1}/{N}: {len(x) / SR:.1f}s (batch)")

    runs, cur = [], []
    for k in missing:
        if cur and (k != cur[-1] + 1 or len(cur) >= batch): runs.append(cur); cur = []
        cur.append(k)
    if cur: runs.append(cur)
    for g in runs: group(g)
    return [np.load(p).astype(np.float32) / 32768 for p in paths]

def file_scenes(project, project_dir):
    """Split the student's own recording at the pauses between scenes."""
    path = os.path.join(project_dir, project["voice"]["file"])
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    hop = SR // 100
    db = np.array([20 * np.log10(np.sqrt(np.mean(x[i:i + hop] ** 2)) + 1e-9) for i in range(0, len(x) - hop, hop)])
    voiced = np.where(db > -40)[0]
    s0, s1 = voiced[0] * 0.01, (voiced[-1] + 1) * 0.01
    runs = []; i = 0; quiet = db < -40
    while i < len(quiet):
        if quiet[i]:
            j = i
            while j < len(quiet) and quiet[j]: j += 1
            if (j - i) * 0.01 >= 0.7 and s0 < i * 0.01 < s1: runs.append(((i + j) / 2) * 0.01)
            i = j
        else: i += 1
    n = len(project["scenes"])
    if len(runs) < n - 1:
        raise SystemExit(f"Your recording has {len(runs)} clear pauses but {n} scenes need {n - 1}. "
                         "Leave a 1 to 2 second pause after every scene and record again.")
    lens = np.array([len(s["vo"]) for s in project["scenes"]], float)
    exp = s0 + np.cumsum(lens)[:-1] / lens.sum() * (s1 - s0)
    picks, last = [], -1
    for e in exp:                      # nearest pause to where the text says the break is, kept in order
        cand = [k for k in range(last + 1, len(runs))]
        k = min(cand, key=lambda k: abs(runs[k] - e)); picks.append(k); last = k
    bounds = [s0] + [runs[k] for k in picks] + [s1]
    return [_trim(x[int(a * SR):int(b * SR)], 0.01) for a, b in zip(bounds, bounds[1:])]

# ------------------------------------------------------------------ voice cloning helpers
def list_voices(key):
    return _req("GET", f"{API}/voices?type=replicated", key).get("voices", [])

def create_voice(key, sample_path, consent_path, name, model=MODEL):
    """Make a replicated voice from a 10 to 30 s sample and the spoken consent line. Returns the voice id."""
    def wav24(p):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", "24000", "-sample_fmt", "s16", "-f", "wav", "-"],
                             capture_output=True, check=True).stdout
        return base64.b64encode(raw).decode()
    body = {"store": True, "voice": {"model": f"models/{model}", "type": "replicated", "display_name": name,
            "replicated": {"source_audio": {"mime_type": "audio/wav", "data": wav24(sample_path)},
                           "consent_audio": {"mime_type": "audio/wav", "data": wav24(consent_path)}}}}
    res = _req("POST", f"{API}/voices", key, body, timeout=300)
    return res.get("id") or res.get("voice", {}).get("id") or res
