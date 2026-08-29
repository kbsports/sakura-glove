# ページと同じ手順で指定図を1枚の画像に描いて、目で確かめるためのもの。
# ブラウザの canvas と同じ順番・同じ合成（source-in で塗る → 線画を multiply）。
import base64
import io
import math
import os
import re
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MAT = os.path.join(ROOT, "キャッチャーミット素材")
PARTS = os.path.join(MAT, "パーツ")

CM_DRAW = [
    ("palm", "palm"), ("backU", "hiradashi"), ("target", "target"), ("web", "web"),
    ("backThumb", "backThumb"), ("backLittle", "backLittle"),
    ("fingercover", "fingercover"), ("hiradashi", "hiradashi"),
    ("binding", "binding"), ("lace", "lace"),
    ("thumbLoop", "thumbLoop"), ("littleLoop", "littleLoop"), ("stitch", "thread"),
]

LOGO_TRIM = {
    "1": dict(box=(48, 126, 673, 504), w=625, h=378, aspect=1.6534),
    "2": dict(box=(159, 199, 1327, 901), w=1168, h=702, aspect=1.6638),
    "3": dict(box=(61, 41, 1700, 860), w=1639, h=819, aspect=2.0012),
}
LOGO_PLACE = {
    "1": dict(cx=0.2153, cy=0.7984, w=0.1167, rot=-10.64),
    "2": dict(cx=0.2153, cy=0.7984, w=0.1177, rot=-10.64),
    "3": dict(cx=0.2121, cy=0.7993, w=0.1328, rot=-10.64),
}

# 試す配色（ページの選択と同じ意味）
COLORS = {
    "body": "#C89568", "palm": "#5C3317", "target": "#CC1111", "web": "#1A2650",
    "backThumb": "#5C3317", "backLittle": "#111111", "fingercover": None,
    "hiradashi": "#F2EEE0", "thumbLoop": None, "littleLoop": None,
    "binding": "#F2EEE0", "lace": "#C89568", "thread": "#FFB800",
}
LOGO = sys.argv[1] if len(sys.argv) > 1 else "2"


def color_of(pid):
    c = COLORS.get(pid)
    if c:
        return c
    if pid == "thread":
        return "#000000"
    return COLORS.get("body")


line = Image.open(os.path.join(MAT, "cm_線あり.png")).convert("L")
W, H = line.size
out = Image.new("RGB", (W, H), "white")

for mask, pid in CM_DRAW:
    hexc = color_of(pid)
    if not hexc:
        continue
    a = np.array(Image.open(os.path.join(PARTS, f"cm_{mask}.png")))[..., 3]
    layer = Image.new("RGB", (W, H), hexc)
    out.paste(layer, (0, 0), Image.fromarray(a))

# 線画を multiply
o = np.array(out).astype(float)
l = np.array(line).astype(float)[..., None] / 255.0
out = Image.fromarray((o * l).astype(np.uint8))

# ロゴ（first-mitt に埋め込まれている画像をそのまま使う）
src = open(os.path.join(ROOT, "first-mitt", "index.html"), encoding="utf-8-sig").read()
i = src.index("const LOGO_PART_IMG = {")
blk = src[i:src.index("\n};", i)]
sec = blk.split(f"'{LOGO}': [")[1].split("],")[0]
sprite = None
for m in re.finditer(r"src:\s*'data:image/png;base64,([^']+)'", sec):
    im = Image.open(io.BytesIO(base64.b64decode(m.group(1)))).convert("RGBA")
    sprite = im if sprite is None else Image.alpha_composite(sprite, im)

tr, pl = LOGO_TRIM[LOGO], LOGO_PLACE[LOGO]
crop = sprite.crop((tr["box"][0], tr["box"][1], tr["box"][0] + tr["w"], tr["box"][1] + tr["h"]))
dw = pl["w"] * W
dh = dw / tr["aspect"]
crop = crop.resize((round(dw), round(dh)), Image.LANCZOS)
crop = crop.rotate(-pl["rot"], resample=Image.BICUBIC, expand=True)
out = out.convert("RGBA")
out.alpha_composite(crop, (round(pl["cx"] * W - crop.width / 2), round(pl["cy"] * H - crop.height / 2)))

p = os.path.join(HERE, f"_プレビュー_ロゴ{LOGO}.png")
out.convert("RGB").save(p)
print("saved:", p)
