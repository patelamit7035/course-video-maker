# project.json reference

```json
{
  "title": "VLOOKUP in 2 Seconds",          // lesson title (top bar, file name)
  "module": "MODULE 2", "lesson": "LESSON 4", // small chips in the top bar (optional)
  "brand": {"accent": "#FFB81C", "theme": "dark", "watermark": "Neha's Excel Academy", "course": "Excel Made Easy"},
  "voice": {"mode": "gemini", "voice_id": "voice_xxx", "batch": 1},   // batch 5 = fewer requests; or {"mode": "file", "file": "me.mp3"} or {"mode": "none"}
  "avatar": {"clips": ["clip1.mp4", "clip2.mp4"]},          // or {"photo": "me.jpg"}; optional
  "captions": true, "caption_keywords": ["VLOOKUP"], "music": true, "music_level": 0.32,
  "scenes": [ ... ]
}
```

Every scene has `type` and `vo` (the spoken line). Optional on every scene: `head` (headline above the visual),
`hold` (extra seconds after the voice), `avatar` ("full" or "bubble"), `caption` (caption text if it should differ from vo).

Items that appear one by one take either plain text or an object; `cue` = a word from this scene's vo (appears when
that word is spoken), `at` = fraction 0 to 1 of the scene's voice.

| type | fields | best for |
| --- | --- | --- |
| `title` | `title`, `subtitle` | opening card |
| `slides` | `title`, `bullets: [text or {text, icon, cue}]` | lists, definitions, formulas |
| `whiteboard` | `layout: list / flow / mindmap / compare / equation`, `title`, `items`; mindmap `center`; compare `left`/`right: {title, points}` | concepts drawn live with a marker |
| `kinetic` | `lines: [{text, style: normal/accent/red/green/muted/strike, icon, cue}]` | hooks, big statements |
| `icons` | `items: [{icon, label, cue}]` | 2 to 8 benefits, features |
| `chart` | `chart: bar / line / pie`, `labels`, `values`, `unit`, `highlight` (index), `title`, `note` | numbers, comparisons |
| `character` | `person: {name, look: {gender, skin: light/medium/dark, hair, outfit}}`, `place: class/office/home/shop/none`, `mood: happy/worried/thinking/excited`, `mood_after`, `say`, `tags`, `pose: stand/sit/point`, `board_text` | stories, examples, problems |
| `flow` | `steps: [{title, sub, icon}]`, `mode: flow / timeline` | processes, step 1-2-3, history |
| `ui` | `device: browser / phone`, `url`, `elements: [{kind: title/text/field/button/card/toast, text, value, type_at, color, cue}]`, `clicks: [{i, cue}]` | software tutorials without screen recording |
| `chat` | `name`, `messages: [{from: me/them, text, cue}]` | conversations, objections, FAQs |
| `quiz` | `question`, `options` (2 to 4), `answer` (index), `reveal_cue` | checks for understanding |
| `compare` | `style: wrong_right / before_after / vs`, `left` / `right: {title, points, cue}` | mistakes, transformations |
| `image` | `file` (screenshot/photo next to project.json), `zoom: {box: [x0,y0,x1,y1], cue}`, `highlights: [{box, label, cue}]`, `caption`, `full` | real screenshots with zoom and callouts |
| `claude` | `prompt`, `marks: [{text, label, cue}]` (parts of the prompt to highlight and name), `type_at`, `type_end`, `reply`, `reply_at`, `files: [{name, meta, cue}]`, `size` | teaching a prompt, showing Claude's answer and files |
| `recap` | `title`, `items` | end of lesson |
| `task` | `minutes`, `steps` | homework |
| `next` | `title`, `label` | next lesson card |

Icons: laptop phone camera mic folder file code chart calendar clock check cross star heart play pause chat person group
teacher bulb rupee money book target rocket trophy search video pen question gear cloud house grid lock key bell warning
excel whatsapp link upload robot wave renew spark bolt.

Boxes in `image` are in the screenshot's own pixels (open it and measure).
