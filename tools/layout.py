#!/usr/bin/env python3
"""Compose every collage as a staggered, gutter-consistent arrangement in which each
photo or clip keeps its exact aspect ratio (nothing is ever cropped).

    python3 tools/layout.py

How a collage is built (per project, and the hero):
  • columns: 2 for up to five items (a wide lead column and a narrower one), 3 for six or
    more; the first item is the lead and spans the wide column (or two columns when there
    are six or more), so the video or key photo reads first;
  • each following item goes to the column that currently ends highest (masonry), with the
    columns starting at different heights and items alternating between full and slightly
    narrower widths, which gives the deliberate scatter of the brief without holes;
  • the result is written as absolute positions (left / top / width in % of the collage
    width) into the CSS between the LAYOUTS markers, and each slot gets
    style="aspect-ratio:W/H" from its own file so its height follows its media.
tools/layouts.json records the generated slots; set "manual": true on a key and edit its
slots to take over by hand. Also inserts the sound / play buttons.
Run after build_images.py, and after editing layouts.json.
"""
import json, os, random, re
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
GUT = 3.4                     # gutter, % of collage width
html = open("index.html").read()
LAY = "tools/layouts.json"
layouts = json.load(open(LAY)) if os.path.exists(LAY) else {}

def aspect(item):
    m = re.search(r'<video[^>]*poster="([^"]+)"', item) or re.search(r'<img src="([^"]+)"', item)
    path = m.group(1)
    if not os.path.exists(path):
        return 1.5, "3/2"
    w, h = Image.open(path).size
    return w / h, f"{w}/{h}"

def scatter(aspects, seed=12, widths=(20, 24, 27, 31, 34), tries=140):
    """Free, deliberately unaligned placement: no columns, no shared edges.

    Each item takes one of a few widths, then we test many random x positions and keep the
    one that sits highest without touching anything already placed (a minimum gap on all
    sides). The seed keeps it stable between runs — change it to reshuffle the scatter."""
    rnd = random.Random(seed)
    placed = []
    for i, a in enumerate(aspects):
        w = widths[rnd.randrange(len(widths))]
        if i == 0:
            w = max(widths)                      # open on a larger piece
        h = w / a
        best = None
        for _ in range(tries):
            x = rnd.uniform(0, 100 - w)
            y = 0.0
            for (px, py, pw, ph) in placed:
                if x < px + pw + GUT and px < x + w + GUT:
                    y = max(y, py + ph + GUT)
            # avoid sharing an edge with anything: nudge off any near-alignment
            for (px, py, pw, ph) in placed:
                if abs(x - px) < 2: x += 2.6
                if abs((x + w) - (px + pw)) < 2: x -= 2.6
            x = min(max(x, 0), 100 - w)
            score = y + rnd.uniform(0, 3.5)      # jitter so it never packs into rows
            if best is None or score < best[0]:
                best = (score, x, y)
        _, x, y = best
        y += rnd.uniform(0, 14) if i else 0      # stagger: tops never line up
        placed.append((x, y, w, h))
    return [(x, y, w) for (x, y, w, h) in placed], None

def compose(aspects, hero=False):
    n = len(aspects)
    if n == 1:
        return [(0, 0, 66)], None
    if hero:
        return scatter(aspects)
    if n <= 5:
        cols = [(0, 60), (60 + GUT, 100 - 60 - GUT)]
        starts = [0, 7]; lead_span = 1
    else:
        w1, w2 = 33, 29.2
        cols = [(0, w1), (w1 + GUT, w2), (w1 + GUT + w2 + GUT, 100 - (w1 + GUT + w2 + GUT))]
        starts = [0, 6, 3]; lead_span = 2
    bottoms = list(starts)
    slots = []
    for i, a in enumerate(aspects):
        if i == 0 and lead_span:
            left = cols[0][0]; width = (cols[lead_span - 1][0] + cols[lead_span - 1][1]) - left
            top = 0; h = width / a
            for c in range(lead_span): bottoms[c] = top + h + GUT
            slots.append((left, top, width)); continue
        c = min(range(len(cols)), key=lambda k: (bottoms[k], k))
        left, cw = cols[c]
        # alternate full / slightly narrower widths for a hand-placed feel
        k = sum(1 for s in slots if abs(s[0] - left) < 0.01 or (left < s[0] < left + cw))
        width = cw if (k % 2 == 0 or n <= 3) else cw * 0.86
        if width != cw and (c == len(cols) - 1 or (i % 2)):
            left = left + (cw - width)          # push narrower items to the column's far edge sometimes
        top = bottoms[c]
        bottoms[c] = top + width / a + GUT
        slots.append((left, top, width))
    return slots, None

def solve(slots, aspects):
    """Final guard: keep DOM order, resolve any overlap by pushing down; returns (bottom, positions%)."""
    placed = []
    for (left, top, width), a in zip(slots, aspects):
        h = width / a
        for (l2, t2, w2, h2) in placed:
            if left < l2 + w2 and l2 < left + width:
                top = max(top, t2 + h2 + GUT)
        placed.append((left, top, width, h))
    bottom = max(t + h for (_, t, _, h) in placed)
    return bottom, [(l, t / bottom * 100, w) for (l, t, w, h) in placed]

css = []
def rebuild(collage_html, key, class_name, hero=False):
    open_tag_m = re.match(r'<(nav|div) class="collage[^"]*"[^>]*>', collage_html)
    tag = open_tag_m.group(1); open_tag = open_tag_m.group(0)
    inner = collage_html[len(open_tag):-len(f"</{tag}>")]
    inner = re.sub(r'\s*<div class="row"[^>]*>|\s*</div>', "", inner)      # unwrap any row markup
    items = [m.group(0) for m in re.finditer(r'<(figure|a) class="ph[^"]*"[^>]*>.*?</\1>', inner, re.S)]
    asp = [aspect(it) for it in items]
    spec = layouts.setdefault(key, {})
    if spec.get("manual") and len(spec.get("slots", [])) == len(items):
        slots = [(s["left"], s["top"], s["width"]) for s in spec["slots"]]
    else:
        slots, _ = compose([a for a, _ in asp], hero)
        spec["slots"] = [{"left": round(l, 2), "top": round(t, 2), "width": round(w, 2)} for l, t, w in slots]
        spec["manual"] = False
    bottom, pos = solve(slots, [a for a, _ in asp])
    out = []
    for it, (a, frac) in zip(items, asp):
        head_end = it.index(">")
        head = re.sub(r'\s*style="[^"]*"', "", it[:head_end]) + f' style="aspect-ratio:{frac}"'
        body = it[head_end:]
        if "<video" in body and 'class="vb' not in body:
            if 'data-autoplay="off"' in body:
                btn = '<button class="vb vb--play" type="button" aria-label="Play with sound">Play</button>'
            elif "data-silent" in body:
                btn = ""
            else:
                btn = '<button class="vb vb--sound" type="button" aria-pressed="false" aria-label="Turn sound on">Sound</button>'
            body = body.replace("</video>", "</video>" + btn, 1)
        out.append("      " + head + body)
    css.append(f"  .{class_name}{{aspect-ratio:100/{bottom:.2f}}}")
    for i, (l, t, w) in enumerate(pos, 1):
        css.append(f"  .{class_name} .ph:nth-child({i}){{left:{l:.2f}%;top:{t:.2f}%;width:{w:.2f}%}}")
    open_tag = re.sub(r'class="collage[^"]*"', f'class="collage {class_name}"', open_tag)
    return open_tag + "\n" + "\n".join(out) + "\n    " + f"</{tag}>"

m = re.search(r'<nav class="collage[^"]*"[^>]*>.*?</nav>', html, re.S)
html = html[:m.start()] + rebuild(m.group(0), "hero", "collage--hero", hero=True) + html[m.end():]
for m in list(re.finditer(r'<article class="project" id="([\w-]+)">.*?</article>', html, re.S)):
    slug, block = m.group(1), m.group(0)
    cm = re.search(r'<div class="collage[^"]*">.*?</div>(?=\s*</article>)', block, re.S)
    block = block[:cm.start()] + rebuild(cm.group(0), slug, f"collage--p-{slug}") + block[cm.end():]
    html = html.replace(m.group(0), block)
json.dump(layouts, open(LAY, "w"), indent=1)
start = html.index("/* LAYOUTS:BEGIN */"); end = html.index("/* LAYOUTS:END */")
html = html[:start] + "/* LAYOUTS:BEGIN */ /* generated by tools/layout.py — edit tools/layouts.json (manual: true) to override */\n" + "\n".join(css) + "\n  " + html[end:]
open("index.html", "w").write(html)
print(f"composed {sum(1 for k in layouts)} collages, {len(css)} rules")
