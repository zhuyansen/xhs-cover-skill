# xhs-cover

[中文](README.md) | English

An Agent Skill for Claude Code (and other tools that support Agent Skills) that makes video covers in the style common on Xiaohongshu (RED, 小红书).

Give it a two-line headline, one number, two or three pieces of evidence and, optionally, a cut-out of a person. Its bundled script lays out three covers from one JSON spec: 3:4 (Xiaohongshu), 16:9 (Bilibili) and 9:16 (Douyin, WeChat Channels). The script needs only Pillow. It makes no network calls and uses no model.

| 3:4 (Xiaohongshu) | 16:9 (Bilibili) |
|---|---|
| ![3:4 example](examples/example-p.jpg) | ![16:9 example](examples/example-h.jpg) |

These are the output of the bundled example, which uses no person and no background picture. With your own cut-out and a background the result is much fuller.

## Who it is for

The skill instructions (`SKILL.md`) and the rules are written in Chinese, because the covers are for Chinese-language platforms and the headline rules are about Chinese text. Claude follows them whatever language you talk to it in. The script itself is language-neutral: it draws whatever text you put in the spec, as long as the font covers it.

## Install

Clone it into your skills folder, with the folder named `xhs-cover`:

```bash
git clone https://github.com/zhuyansen/xhs-cover-skill ~/.claude/skills/xhs-cover
```

For other tools that support Agent Skills, put it wherever that tool looks for skills.

You need Python 3.9 or later and Pillow:

```bash
python3 -m pip install pillow
```

The script looks for a heavy CJK font on its own (Hiragino Sans GB on macOS, Microsoft YaHei on Windows, Noto Sans CJK on Linux). If it finds none it stops and says how to install one; you can also point the `font` field of the spec at a font file. On Linux without a CJK font:

```bash
sudo apt install fonts-noto-cjk
```

Tested on macOS and on Linux (Debian with Noto Sans CJK). The Windows font paths are the system defaults and have not been tested; if they fail, set `font`.

## Use

Once installed, ask Claude for a cover and give it the main points of your video, for example: "make a Xiaohongshu cover for this video". You can also run the script directly:

```bash
cd examples
python3 ../scripts/cover.py spec.json --thumb
```

A spec looks like this. Only `line1` and `line2` are required:

```json
{"out": "cover",
 "line1": "我装了 512 个 Skill", "line2": "只用过 51 个",
 "person": "me.png", "background": "bg.png",
 "cards": [{"image": "shot.png"},
           {"small": "删 461 个，省 token", "big": "3.8 万"},
           {"small": "14 个安装工具", "big": "12 个不设防", "color": "#FF5A5A"}],
 "question": "该用哪个？"}
```

| Field | What it is |
|---|---|
| `line1` | The subject, in white, on one line |
| `line2` | The hook, in the accent colour and much larger. Shorter is bigger |
| `person` | A cut-out PNG with a transparent background. Optional |
| `background`, `background_h` | Any picture without text or people; a separate one for 16:9 if you like. Left out, you get a dark gradient with a glow in the accent colour |
| `cards` | Up to three pieces of evidence: a screenshot (`image`), or a small label over a big value (`small`, `big`). `color` defaults to the accent |
| `question` | A short question on a colour block at the bottom left. Optional |
| `accent`, `shadow`, `dim`, `font` | Headline colour, its offset shadow, how much to darken the picture, a font file |

Outputs are `<out>-p.jpg` (1242×1656), `<out>-h.jpg` (1920×1080) and `<out>-v.jpg` (1080×1920). `--thumb` adds a 320-pixel-wide copy of the 3:4 cover, which is roughly its size in a feed: if the big line cannot be read there, the cover is not working. The 9:16 file is the 3:4 cover placed on a blurred copy of itself, so nothing gets cropped.

## What is inside

| File | Contents |
|---|---|
| `SKILL.md` | The four things to settle before making a cover, the command, and the checks to run on the result |
| `scripts/cover.py` | The layout script: JSON in, JPEG out |
| `references/rules.md` | Six rules and the reasons for them, the layout, a second "wish" style of cover, common mistakes, a pre-delivery checklist |
| `references/background-prompt.md` | A prompt for an image model that produces a background with no text and no people |
| `examples/` | An example that runs with no assets at all |

## The rules in brief

1. The headline takes a fifth to a third of the cover: two lines, the second in a bright colour and much larger, heavy type with a thick black outline.
2. If there is a person, they fill about half the height, with a strong expression. Use the same face on every cover: it is how people recognise the account.
3. Show evidence instead of explaining: screenshots, results, a number on a card. Two or three items.
4. One number in the hook, and it must be a number the video actually contains. A cover is a promise.
5. As little small text as possible.
6. A saturated, lit background and few colours: besides white, no more than three.

The skill also tells Claude to stop and ask when it has not been given a real number, and to open and check every image before saying it is done.

## What it does not do

- It does not cut people out of photos. Bring your own transparent PNG (on an iPhone, press and hold the person in Photos and choose Copy Subject; on a Mac, use Remove Background in Preview).
- It does not generate backgrounds. Use any image model, or none.
- It does not promise clicks. The rules are patterns observed in a set of high-engagement covers, not laws; check them against your own results from one post to the next.
- It is not for YouTube. YouTube thumbnails tend to do better with very little text, the opposite of what works here.

## Licence

MIT
