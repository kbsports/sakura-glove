# kokunai/catcher-mitt/index.html を組み立てる（国内工場版）。
#
#   _part_head.html   … <head>とCSS（first-mitt からそのまま持ってきてタイトルだけ変えたもの）
#   _part_body.html   … 画面のHTML
#   _part_script.html … JavaScript（__LOGO_PART_IMG__ の所に画像を差し込む）
#
# 差し込む画像
#   ・ロゴのパーツ画像 … first-mitt/index.html の LOGO_PART_IMG をそのまま持ってくる
#   ・線画 CM_LINE     … キャッチャーミット素材/cm_線あり.png を4階調に落としたもの
#   ・パーツ CM_MASKS  … キャッチャーミット素材/パーツ/cm_*.png（黒一色・背景透過）
#
# 画像は外部ファイルにせず、全部このHTMLの中に埋め込む。
# アップロードは index.html 1枚で済み、フォルダの入れ子で事故らない。
import base64
import io
import os
import re

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))   # 桜グラブシミュレーション用
MAT = os.path.join(ROOT, "キャッチャーミット素材")
PARTS = os.path.join(MAT, "パーツ")
FMITT = os.path.join(ROOT, "kokunai", "first-mitt", "index.html")

# 描く順番（_part_script.html の CM_DRAW とそろえること）
MASK_NAMES = ["palm", "backU", "target", "web", "backThumb", "backLittle",
              "fingercover", "hiradashi", "binding", "lace",
              "thumbLoop", "littleLoop", "stitch"]


def b64png(im, **kw):
    buf = io.BytesIO()
    im.save(buf, format="PNG", optimize=True, **kw)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def build_line():
    """表示用の線画。4階調に落として軽くする（532KB → 70KB）。
    真っ白にはせず薄いグレーを残すので、縮小表示でも線がガタつかない。"""
    a = np.array(Image.open(os.path.join(MAT, "cm_線あり.png")).convert("L"))
    n = 4
    lv = np.linspace(0, 255, n)
    idx = np.clip(np.round(a.astype(float) / 255 * (n - 1)), 0, n - 1).astype(int)
    im = Image.fromarray(lv[idx].astype(np.uint8), "L")
    return im.convert("P", palette=Image.ADAPTIVE, colors=n)


def logo_block():
    """first-mitt から const LOGO_PART_IMG = {...}; をまるごと取り出す。"""
    s = open(FMITT, encoding="utf-8-sig").read()
    i = s.index("const LOGO_PART_IMG = {")
    j = s.index("\n};", i) + len("\n};")
    return s[i:j]


line_im = build_line()
line_b64 = b64png(line_im)
print(f"線画 {line_im.size} → {len(line_b64):,} 文字")

masks = []
for k in MASK_NAMES:
    p = os.path.join(PARTS, f"cm_{k}.png")
    im = Image.open(p)
    px = int((np.array(im)[..., 3] > 0).sum())
    masks.append(f"  {k!r}: '{b64png(im)}',")
    print(f"  {k:12s} {px:8,}px  {os.path.getsize(p):7,}B")

# ---- クローズバックの指定図（背面＝新しい絵／捕球面＝いまの絵）------------
CB = os.path.join(MAT, "クローズバック背面", "合成")
CB_PARTS = os.path.join(CB, "パーツ")
CB_MASK_NAMES = ["palm", "target", "web", "thumb", "middle", "ringPinky", "base",
                 "fingercover", "fingerout", "belt", "hamidashi",
                 "binding", "lace", "thumbLoop", "littleLoop", "stitch"]


def build_line4(path):
    """表示用の線画。4階調に落として軽くする。"""
    a = np.array(Image.open(path).convert("L"))
    n = 4
    lv = np.linspace(0, 255, n)
    idx = np.clip(np.round(a.astype(float) / 255 * (n - 1)), 0, n - 1).astype(int)
    im = Image.fromarray(lv[idx].astype(np.uint8), "L")
    return im.convert("P", palette=Image.ADAPTIVE, colors=n)


cb_line_im = build_line4(os.path.join(CB, "cb2_線あり.png"))
cb_line_b64 = b64png(cb_line_im)
print(f"\nクローズバック線画 {cb_line_im.size} → {len(cb_line_b64):,} 文字")

cb_masks = []
for k in CB_MASK_NAMES:
    p = os.path.join(CB_PARTS, f"cb2_{k}.png")
    im = Image.open(p)
    px = int((np.array(im)[..., 3] > 0).sum())
    cb_masks.append(f"  {k!r}: '{b64png(im)}',")
    print(f"  {k:12s} {px:8,}px  {os.path.getsize(p):7,}B")

inject = (
    logo_block() + "\n\n"
    "/* 指定図の線画（表示用・破線ステッチは抜いてある） */\n"
    f"const CM_LINE = '{line_b64}';\n\n"
    "/* パーツのマスク（黒一色・背景透過）。source-in で選択色に塗って重ねる */\n"
    "const CM_MASKS = {\n" + "\n".join(masks) + "\n};\n\n"
    "/* クローズバックの指定図（左＝背面 ca.png 由来／右＝いまの捕球面） */\n"
    f"const CB_LINE = '{cb_line_b64}';\n\n"
    "const CB_MASKS = {\n" + "\n".join(cb_masks) + "\n};\n"
)

head = open(os.path.join(HERE, "_part_head.html"), encoding="utf-8-sig").read()
body = open(os.path.join(HERE, "_part_body.html"), encoding="utf-8-sig").read()
script = open(os.path.join(HERE, "_part_script.html"), encoding="utf-8-sig").read()
if "__LOGO_PART_IMG__" not in script:
    raise SystemExit("_part_script.html に __LOGO_PART_IMG__ がない")
script = script.replace("__LOGO_PART_IMG__", inject)

out = os.path.join(HERE, "index.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(head + body + "\n" + script)
print(f"\nsaved: {out}  {os.path.getsize(out):,} バイト")
