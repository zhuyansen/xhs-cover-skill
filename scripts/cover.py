#!/usr/bin/env python3
"""Compose a Xiaohongshu-style video cover from a small JSON spec. Needs only Pillow.

  python3 cover.py spec.json                # → <out>-p.jpg (3:4, 1242×1656), <out>-h.jpg (16:9, 1920×1080), <out>-v.jpg (9:16, 1080×1920)
  python3 cover.py spec.json --only p       # one layout
  python3 cover.py spec.json --thumb        # also <out>-p-thumb.jpg at 320 px wide (made with the 3:4 cover): if the big line cannot be read there, the cover fails

The 9:16 file is the 3:4 cover placed on a blurred copy of itself, not a separate layout, so nothing gets cropped on Douyin or WeChat Channels.
Without a person the evidence cards become wide rows and fill the frame; with a person they stack on the left.

The spec (every path is relative to the spec file; only "line1" and "line2" are required):

  {"out": "cover",
   "line1": "我装了 512 个 Skill",              the subject, white, one line, up to about 10 (a Latin letter, digit or space counts half)
   "line2": "只用过 51 个",                     the hook, in the accent colour; up to about 7, biggest at 4–5 (a Latin letter, digit or space counts half)
   "accent": "#FFD84A", "shadow": "#2F6BFF",  hook colour and the colour of its offset shadow
   "background": "bg.png",                    any picture without text or people; or leave it out for a dark gradient
   "background_h": "bg-h.png",                optional separate picture for the 16:9 layout
   "dim": 0.35,                               how much to darken the picture, 0–1
   "person": "me.png",                        a cut-out with a transparent background; left out = a cover without a person
   "cards": [                                 up to three pieces of evidence; "color" defaults to the accent
     {"image": "shot.png", "color": "#3EE08F"},
     {"small": "删 461 个，省 token", "big": "3.8 万", "color": "#3EE08F"},
     {"small": "14 个安装工具", "big": "12 个不设防", "color": "#FF5A5A"}],
   "question": "该用哪个？",                    optional bottom-left hook on a colour block, up to 6 characters
   "font": "/path/to/a/heavy/CJK/font"}       optional; otherwise the first heavy CJK font found on the machine

It draws what the spec says and nothing else: the numbers on a cover are claims, so they must come from the film or the post.
"""
import json, os, sys, argparse
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

# (path, face index). In a .ttc the index picks the face: Simplified Chinese where the collection has several languages.
FONTS = [("/System/Library/Fonts/Hiragino Sans GB.ttc", 2), ("/System/Library/Fonts/Hiragino Sans GB.ttc", 0), ("/System/Library/Fonts/PingFang.ttc", 8), ("/System/Library/Fonts/STHeiti Medium.ttc", 0),
         ("C:/Windows/Fonts/msyhbd.ttc", 0), ("C:/Windows/Fonts/simhei.ttf", 0), ("/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc", 2), ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 2),
         ("/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc", 2), ("/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc", 2)]
ap = argparse.ArgumentParser(); ap.add_argument("spec"); ap.add_argument("--only", choices=["p", "h", "v"]); ap.add_argument("--thumb", action="store_true"); a = ap.parse_args()
S = json.load(open(a.spec)); BASE = os.path.dirname(os.path.abspath(a.spec)); rel = lambda p: p if os.path.isabs(p) else os.path.join(BASE, p)
if not S.get("line1") or not S.get("line2"): sys.exit("spec needs line1 and line2")
def pick_font():
    if S.get("font"): return rel(S["font"]), 0
    for p, i in FONTS:
        if os.path.exists(p):
            try: ImageFont.truetype(p, 40, index=i); return p, i
            except Exception: continue
    import glob                                                         # not at a known path: look through the usual font folders for a CJK family, heaviest first
    roots = ["/usr/share/fonts", "/usr/local/share/fonts", os.path.expanduser("~/.fonts"), os.path.expanduser("~/.local/share/fonts"), os.path.expanduser("~/Library/Fonts"), "/Library/Fonts", "C:/Windows/Fonts"]
    found = [f for r in roots for f in glob.glob(os.path.join(r, "**", "*"), recursive=True) if f.lower().endswith((".ttf", ".ttc", ".otf"))]
    for want in ("black", "heavy", "bold", "medium", ""):
        for f in found:
            n = os.path.basename(f).lower()
            if any(k in n for k in ("notosanscjk", "notosanssc", "sourcehansans", "source han sans", "msyh", "simhei", "wqy", "pingfang", "hiragino", "heiti")) and want in n:
                i = 2 if "notosanscjk" in n and n.endswith(".ttc") else 0     # in the Noto CJK collection, face 2 is Simplified Chinese
                try: ImageFont.truetype(f, 40, index=i); return f, i
                except Exception: continue
    sys.exit("no CJK font found. Install one (Debian/Ubuntu: apt install fonts-noto-cjk) or set \"font\" in the spec to a .ttf/.ttc/.otf path")
FP, FI = pick_font(); font = lambda size: ImageFont.truetype(FP, max(8, int(size)), index=FI)
rgb = lambda h: tuple(int(h.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
ACC, SHD = S.get("accent", "#FFD84A"), S.get("shadow", "#2F6BFF")

def fit(text, max_w, max_size, stroke):
    """the largest size at which the text stays on one line"""
    size = max_size
    while size > 24:
        l, t, r, b = font(size).getbbox(text, stroke_width=stroke(size))
        if r - l <= max_w: break
        size -= 4
    return size
def text_layer(text, size, fill, stroke_w, shadow=None, off=0, angle=0):
    """one line of outlined text on its own transparent layer, optionally with a hard offset shadow and a tilt"""
    f = font(size); l, t, r, b = f.getbbox(text, stroke_width=stroke_w); pad = stroke_w + abs(off) + 12
    im = Image.new("RGBA", (r - l + pad * 2, b - t + pad * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(im); o = (pad - l, pad - t)
    if shadow: d.text((o[0] + off, o[1] + off), text, font=f, fill=rgb(shadow), stroke_width=stroke_w, stroke_fill=rgb(shadow))
    d.text(o, text, font=f, fill=rgb(fill), stroke_width=stroke_w, stroke_fill=(0, 0, 0))
    return im.rotate(angle, expand=True, resample=Image.BICUBIC) if angle else im
def cover_fit(im, w, h):
    s = max(w / im.width, h / im.height); im = im.resize((round(im.width * s) + 1, round(im.height * s) + 1), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2; return im.crop((x, y, x + w, y + h))
def backdrop(w, h, key):
    p = S.get(key) or S.get("background")
    if p: bg = cover_fit(Image.open(rel(p)).convert("RGB"), w, h)
    else:                                                               # no picture: a dark vertical gradient with a soft glow in the accent colour
        bg = Image.new("RGB", (w, h)); px = ImageDraw.Draw(bg)
        for y in range(h): px.line([(0, y), (w, y)], fill=tuple(int(c0 + (c1 - c0) * y / h) for c0, c1 in zip((16, 22, 40), (6, 8, 14))))
        glow = Image.new("RGB", (w, h), (0, 0, 0)); ImageDraw.Draw(glow).ellipse([w * 0.1, h * 0.25, w * 0.9, h * 0.75], fill=tuple(int(c / 2.2) for c in rgb(ACC)))
        bg = ImageChops.add(bg, glow.filter(ImageFilter.GaussianBlur(w // 5)))
    dim = float(S.get("dim", 0.35 if p else 0.0)); bg = Image.blend(bg, Image.new("RGB", (w, h), (0, 0, 0)), dim).convert("RGBA")
    top = Image.new("L", (1, h)); top.putdata([int(150 * max(0, 1 - y / (h * 0.36))) for y in range(h)])   # darker behind the headline so it reads on any picture
    bg.alpha_composite(Image.merge("RGBA", (*Image.new("RGB", (w, h), (0, 0, 0)).split(), top.resize((w, h))))); return bg
def sticker(path, height, outline):
    """the cut-out with a white sticker edge and a soft shadow"""
    im = Image.open(rel(path)).convert("RGBA"); bb = im.split()[3].point(lambda v: 255 if v > 24 else 0).getbbox(); im = im.crop(bb) if bb else im   # ignore faint leftovers of the cut-out
    s = height / im.height; im = im.resize((max(1, round(im.width * s)), height), Image.LANCZOS); pad = outline * 3
    canvas = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0)); canvas.alpha_composite(im, (pad, pad)); alpha = canvas.split()[3]
    edge = alpha.filter(ImageFilter.MaxFilter(outline * 2 + 1)).filter(ImageFilter.GaussianBlur(1.2)).point(lambda v: 255 if v > 110 else 0).filter(ImageFilter.GaussianBlur(0.8))
    out = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    out.alpha_composite(Image.merge("RGBA", (*Image.new("RGB", canvas.size, (0, 0, 0)).split(), edge.filter(ImageFilter.GaussianBlur(outline)).point(lambda v: int(v * 0.55)))), (0, 0))
    out.alpha_composite(Image.merge("RGBA", (*Image.new("RGB", canvas.size, (255, 255, 255)).split(), edge))); out.alpha_composite(canvas); return out, pad
def card(c, w, angle, flat=False):
    """a piece of evidence: a screenshot in a coloured frame, or a small label over a big value"""
    col = rgb(c.get("color", ACC)); bw = max(5, w // 70); rad = w // 22
    if c.get("image"):
        im = Image.open(rel(c["image"])).convert("RGB"); h = min(round(w * im.height / im.width), round(w * 1.25)); im = cover_fit(im, w - bw * 2, h - bw * 2)
        box = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(box).rounded_rectangle([0, 0, w - 1, h - 1], rad, fill=col + (255,))
        m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, im.width - 1, im.height - 1], max(2, rad - bw), fill=255); box.paste(im, (bw, bw), m)
    else:
        px = w // 16; small, big = c.get("small", ""), c.get("big", "")
        if flat:
            px = w // 22; fb = fit(big, w * 0.5, w // 7.5, lambda s: 0) if big else 0; fs = fit(small, w - px * 3 - (font(fb).getlength(big) if big else 0), w // 15, lambda s: 0) if small else 0
            h = px * 2 + int(max(fb, fs) * 1.2); box = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(box); d.rounded_rectangle([0, 0, w - 1, h - 1], rad // 2, fill=(10, 14, 22, 235), outline=col + (255,), width=bw)
            if small: d.text((px, h // 2), small, font=font(fs), fill=(255, 255, 255), anchor="lm")
            if big: d.text((w - px, h // 2), big, font=font(fb), fill=col, anchor="rm")
        else:
            fs = fit(small, w - px * 2, w // 9, lambda s: 0) if small else 0; fb = fit(big, w - px * 2, w // 5.2, lambda s: 0) if big else 0
            h = px * 2 + (int(fs * 1.25) if small else 0) + (int(fb * 1.2) if big else 0)
            box = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(box); d.rounded_rectangle([0, 0, w - 1, h - 1], rad, fill=(10, 14, 22, 235), outline=col + (255,), width=bw); y = px
            if small: d.text((px, y), small, font=font(fs), fill=(255, 255, 255)); y += int(fs * 1.25)
            if big: d.text((px, y), big, font=font(fb), fill=col)
    sh = Image.new("RGBA", (box.width + 40, box.height + 40), (0, 0, 0, 0)); sh.alpha_composite(Image.merge("RGBA", (*Image.new("RGB", box.size, (0, 0, 0)).split(), box.split()[3].point(lambda v: int(v * 0.5)))), (26, 28))
    sh = sh.filter(ImageFilter.GaussianBlur(10)); sh.alpha_composite(box, (20, 20)); return sh.rotate(angle, expand=True, resample=Image.BICUBIC)
def question(text, size):
    f = font(size); l, t, r, b = f.getbbox(text); px, py = size // 3, size // 5
    im = Image.new("RGBA", (r - l + px * 2, b - t + py * 2), rgb(ACC) + (255,)); ImageDraw.Draw(im).text((px - l, py - t), text, font=f, fill=(12, 12, 12)); return im.rotate(3, expand=True, resample=Image.BICUBIC)

def compose(w, h, wide):
    im = backdrop(w, h, "background_h" if wide else "background"); u = h / 1656 if not wide else h / 1080; mx = round(w * 0.048)
    has_p = bool(S.get("person")); cards = (S.get("cards") or [])[:3]
    side = wide and not has_p and bool(cards)                            # 16:9 without a person: headline left, evidence in a column on the right, so the right third is not left empty
    title_w = (w - mx * 2) if not wide else round(w * (0.56 if has_p else 0.5 if side else 0.9))
    s1 = fit(S["line1"], title_w, (116 if not wide else 104) * u, lambda s: round(s * 0.16)); s2 = fit(S["line2"], title_w, (236 if not wide else 196) * u, lambda s: round(s * 0.13))
    y = round((64 if not wide else 46) * u)
    t1 = text_layer(S["line1"], s1, "#FFFFFF", round(s1 * 0.16)); im.alpha_composite(t1, (mx - round(s1 * 0.16) - 12, y)); y += round(s1 * 1.22)
    t2 = text_layer(S["line2"], s2, ACC, round(s2 * 0.13), SHD, round(s2 * 0.05), 3); im.alpha_composite(t2, (mx - round(s2 * 0.13) - 12, y - round(s2 * 0.1))); y += t2.height - round(s2 * 0.1) + round(24 * u)   # below the tilted line and its shadow
    if has_p:                                                           # the person takes the lower right, about half the height (3:4) or most of it (16:9)
        ph = round(h * (0.66 if not wide else 0.9)); st, pad = sticker(S["person"], ph, max(8, round(18 * u)))
        px_ = w - st.width + pad - round(w * 0.01); py_ = h - st.height + pad
        if px_ < w * 0.34: px_ = round(w * 0.34)                        # a very wide cut-out is pushed right rather than covering the evidence
        im.alpha_composite(st, (px_, py_)); left_w = px_ + pad - mx - round(w * 0.02)
    else: left_w = w - mx * 2
    qh = 0
    if S.get("question"):
        q = question(S["question"], round((92 if not wide else 78) * u)); qh = q.height + round(40 * u); im.alpha_composite(q, (mx, h - q.height - round(60 * u)))
    if cards:                                                           # evidence between the headline and the bottom hook, alternately tilted and nudged
        area_h = h - y - qh - round(50 * u)
        if side:                                                        # a column of wide rows on the right, centred top to bottom
            cw = round(w * 0.36); x = w - mx - cw; made_ = [card(c, cw, (-1.2, 1, -0.8)[k], flat=not c.get("image")) for k, c in enumerate(cards)]
            for cd in made_: cd.thumbnail((cd.width, (h - round(120 * u)) // len(made_)), Image.LANCZOS)
            gap = round(22 * u); tot = sum(cd.height for cd in made_) + gap * (len(made_) - 1); yy = (h - tot) // 2
            for cd in made_: im.alpha_composite(cd, (x + (cw - cd.width) // 2, yy)); yy += cd.height + gap
        elif wide:                                                      # side by side
            n = len(cards); cw = min(round((left_w - (n - 1) * 24 * u) / n), round(w * (0.3 if has_p else 0.46))); x = mx   # without a person the cards may spread across the frame
            for k, c in enumerate(cards):
                cd = card(c, cw, (-3, 2, -2)[k]); cd.thumbnail((cd.width, max(60, area_h)), Image.LANCZOS); im.alpha_composite(cd, (x, y + round((0, 26, 8)[k] * u))); x += cw + round(24 * u)
        else:                                                           # stacked on the left of the person
            cw = max(160, min(round(left_w * 0.98), round(w * (0.56 if has_p else 0.9)))); each = area_h // len(cards); yy = y + round(10 * u)
            for k, c in enumerate(cards):
                cd = card(c, cw if not c.get("image") else round(cw * 0.86), (-3, 2, -2)[k] if has_p else (-1.2, 1, -0.8)[k], flat=not has_p and not c.get("image")); cd.thumbnail((cd.width, max(60, each)), Image.LANCZOS)
                im.alpha_composite(cd, (mx + round((0, 34, 8)[k] * u) if has_p else (w - cd.width) // 2, yy)); yy += min(cd.height - round(14 * u), each) if has_p else min(cd.height + round(18 * u), each)
    return im.convert("RGB")

out = rel(S.get("out", "cover")); made = []
if a.only in (None, "p", "v"):
    p = compose(1242, 1656, False)
    if a.only in (None, "p"): p.save(out + "-p.jpg", quality=92); made.append(out + "-p.jpg")
    if a.thumb and a.only in (None, "p"): t = p.resize((320, 427), Image.LANCZOS); t.save(out + "-p-thumb.jpg", quality=88); made.append(out + "-p-thumb.jpg")
    if a.only in (None, "v"):                                           # 9:16 = the 3:4 cover on a blurred, darkened copy of itself, so nothing is cropped
        bg = cover_fit(p.resize((270, 360)), 270, 480).filter(ImageFilter.GaussianBlur(24)).resize((1080, 1920)); bg = Image.blend(bg, Image.new("RGB", bg.size, (0, 0, 0)), 0.3)
        fg = p.resize((1080, 1440), Image.LANCZOS); m = Image.new("L", (1, 1440)); m.putdata([min(255, y * 4, (1439 - y) * 4) for y in range(1440)])   # fade the top and bottom 64 px into the blur: no hard seam
        bg.paste(fg, (0, 240), m.resize((1080, 1440))); bg.save(out + "-v.jpg", quality=92); made.append(out + "-v.jpg")
if a.only in (None, "h"): compose(1920, 1080, True).save(out + "-h.jpg", quality=92); made.append(out + "-h.jpg")
print("\n".join(made)); print(f"font: {os.path.basename(FP)}")
