---
name: course-video-maker
description: Turn a lesson script into a finished MP4 course video (whiteboard, animation, slides, charts, chat, quiz and more) with captions, music and the user's own voice. No camera.
---

# Course Video Maker

Makes faceless lesson videos for online courses. The user gives a topic or a script; you write a `project.json`
(scenes + voiceover lines), check a preview, and render a 1920x1080 MP4 with voiceover, Hinglish/English captions,
music, sound effects and the user's watermark.

## Before you start (once per user)

1. Code execution must be on: Settings > Capabilities > "Code execution and file creation".
2. For the Gemini voice, network access must be on: Settings > Capabilities > "Allow network egress".
   If a voice call fails with "Cannot reach Gemini", tell the user exactly this and offer the `file` or `none` voice mode.
3. Voice options (ask the user which one, once):
   - **Gemini cloned voice** (recommended): user's Gemini API key from aistudio.google.com saved as `gemini_key.txt`
     in the project folder (never print it, never put it in project.json). Voice id from `python3 make_video.py voices`.
     No clone yet: the user records two clips (10 to 30 s of natural speech, and the consent line
     "I am the owner of this voice and I consent to Google using this voice to create a synthetic voice model.")
     and you run `python3 make_video.py clone sample.wav consent.wav "My voice"`.
     Daily limit hit ("daily limit")? The engine switches to `gemini-3.8-flash-lite-tts` (same voice). To use fewer
     requests, add `"batch": 5` to `voice` (reads 5 scenes per request and cuts them apart safely).
   - **Own recording**: the user reads all scene lines in one file with a 1 to 2 second pause after each scene.
   - **No voice**: captions and music only.

## Workflow

`SKILL_DIR` below = the folder this SKILL.md is in. Work in your own folder (one folder per lesson),
never inside SKILL_DIR.

1. **Script first.** If the user has only a topic, research it and write the lesson script with them before any video.
   Explain like to a 15-year-old: example before rule, one idea per scene, daily-life analogy, short sentences.
2. **Write `project.json`** in a working folder (copy the skill's `scripts/` path into commands). Read
   `reference.md` for every scene type and its fields. Rules:
   - One scene = one idea, 1 to 3 spoken sentences in `vo`. Write `vo` the way it is spoken.
   - On-screen text (`head`, bullets, labels) stays short; the voice carries the detail.
   - Use `cue` (a word from that scene's `vo`) to make an item appear exactly when the word is said.
   - Mix types; never more than 3 scenes of the same type in a row.
   - Avatar (optional, only if the user gives a photo or clips): `"avatar": "full"` or `"bubble"` on a scene shows the
     face for 1.5 s. Use it on the first scene, a few key moments, and the last scene. The engine keeps 20 s between cuts.
3. **Check**: `python3 SKILL_DIR/scripts/make_video.py check project.json`
4. **Preview** (fast, no voice): `python3 SKILL_DIR/scripts/make_video.py preview project.json` and LOOK at `preview.png`.
   Fix overlaps, empty scenes, text too long. Use `still project.json N` for one scene at full size.
5. **Render**: `python3 SKILL_DIR/scripts/make_video.py render project.json --budget 240`
   It makes the voice, then renders scene by scene. If it prints `PAUSED`, run the same command again; finished
   scenes are kept. Repeat until it prints `DONE`.
6. **Deliver** the MP4 (and the .srt captions file) to the user. Files over 30 MB cannot be sent in chat: render with
   `--crf 26`, or split the lesson into two projects.

## Changing a video

Edit only the scenes that change in `project.json` and render again: unchanged scenes are reused, and the voice is
re-made only for scenes whose `vo` changed. Typical asks: "scene 3 slow karo" (add `"hold": 2`), "color badlo"
(`brand.accent`), "light background" (`brand.theme: "light"`), "ye word highlight karo" (`caption_keywords`).

## Files

- `scripts/make_video.py`: the command line (check, preview, still, voice, render, voices, clone)
- `reference.md`: every scene type, its fields and an example
- `templates/`: ready projects to copy (`all_types.json` shows every type once)
- `assets/fonts/`: fonts used by the videos (open licences in the same folder)
