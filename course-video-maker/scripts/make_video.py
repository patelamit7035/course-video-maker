"""Course Video Maker: turn a project.json (scenes + voiceover lines) into an MP4 lesson video.

  python3 make_video.py check   project.json            # validate, list scenes and estimated length
  python3 make_video.py preview project.json            # preview.png: 2 stills per scene (fast, no voice)
  python3 make_video.py still   project.json 4 [0.6]    # one full-size still of scene 4
  python3 make_video.py voice   project.json            # make the voiceover only (cached per scene)
  python3 make_video.py render  project.json [--budget 240] [--crf 21] [--procs 2]
        renders scene by scene; if it prints PAUSED, run the same command again (finished scenes are kept)
  python3 make_video.py voices                          # list your Gemini cloned voices
  python3 make_video.py clone sample.wav consent.wav "My voice"   # create a Gemini cloned voice
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cvm"))
import engine as E
import voice as VO

def arg(name, default=None, cast=str):
    return cast(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default

def main():
    if len(sys.argv) < 2: print(__doc__); return
    cmd = sys.argv[1]
    if cmd == "voices":
        for v in VO.list_voices(VO.gemini_key(os.getcwd())): print(v.get("id"), " ", v.get("display_name"))
        return
    if cmd == "clone":
        vid = VO.create_voice(VO.gemini_key(os.getcwd()), sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "My voice")
        print("VOICE ID:", vid); return
    path = sys.argv[2]
    if cmd == "check":
        pj = E.load(path); tl = E.timeline(pj, None)
        for sc in tl["scenes"]: print(f"  {sc['i'] + 1:2d}. {sc['s']['type']:<10} {sc['dur']:5.1f}s  {sc['s'].get('head', '')}")
        print(f"OK: {len(tl['scenes'])} scenes, about {tl['total'] / 60:.1f} min (real length follows the voice); avatar cuts: {len(tl['pops'])}")
    elif cmd == "preview": E.preview(path, with_voice="--voice" in sys.argv)
    elif cmd == "still": print(E.still(path, int(sys.argv[3]), float(sys.argv[4]) if len(sys.argv) > 4 else 0.6))
    elif cmd == "voice":
        pj = E.load(path); clips = E.voice_clips(pj)
        print("VOICE OK:", sum(len(c) for c in clips) / 24000 if clips else 0, "seconds")
    elif cmd == "render":
        ok = E.render(path, budget=arg("--budget", None, float), procs=arg("--procs", None, int), crf=arg("--crf", 21, int))
        sys.exit(0 if ok else 3)
    else: print(__doc__)

if __name__ == "__main__":
    main()
