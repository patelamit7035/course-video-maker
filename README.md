# course-video-maker

A Claude skill that turns a lesson script into a finished MP4 course video, without a camera: whiteboard, slides,
kinetic text, icons, charts, character stories, flowcharts, software screens, chat, quiz and compare scenes, with
captions, music, sound effects and the creator's own (Gemini cloned) voice.

Made for the course **Build Your Course Using AI** (One Man Business School by Amit Patel).

## Install in Claude
1. Settings > Capabilities: turn on **Code execution and file creation**, and **Allow network egress** with **All domains** (needed for the Gemini voice).
2. Zip the `course-video-maker/` folder (`zip -r course-video-maker.zip course-video-maker -x '*/__pycache__/*'`).
3. Settings > Customize > Skills > Add > Upload skill, and choose the zip (do not unzip it).
4. New chat: "Use the course-video-maker skill and make a short whiteboard video about ..."

## Command line
```
python3 course-video-maker/scripts/make_video.py check   project.json
python3 course-video-maker/scripts/make_video.py preview project.json
python3 course-video-maker/scripts/make_video.py render  project.json --budget 240
```
`course-video-maker/reference.md` lists every scene type and field; `demo/project.json` is a sample lesson.

## Voice
Put your Gemini API key in `gemini_key.txt` next to `project.json` (never commit it; it is git-ignored).
Set `"voice": {"mode": "gemini", "voice_id": "voice_..."}`. Add `"batch": 5` to use fewer requests when the
daily limit is small. Other modes: `{"mode": "file", "file": "me.mp3"}` or `{"mode": "none"}`.

## Fonts
Inter, Inter Display, Kalam and DejaVu Sans Mono, under their open licences in `course-video-maker/assets/fonts/`.
