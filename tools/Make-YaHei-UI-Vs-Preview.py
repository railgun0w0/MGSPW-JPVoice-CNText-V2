#!/usr/bin/env python3
"""Create the missing visual comparison sheet from existing XPRs."""

from pathlib import Path
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.pc_crypto import filename_seed, outer_transform
from core.xpr_font import XprFont


W, H, SCALE = 58, 67, 4
REFS = [("U+660F", 0x660F), ("U+7729", 0x7729), ("U+6655", 0x6655), ("U+68D2", 0x68D2), ("U+5668", 0x5668), ("U+53A2", 0x53A2), ("U+538C", 0x538C), ("U+51B3", 0x51B3), ("U+5377", 0x5377)]


def load(path: Path) -> XprFont:
    return XprFont(outer_transform(path.read_bytes(), filename_seed(path.name)))


def extract(font: XprFont, index: int) -> bytes:
    r = font.font_data.glyphs[index]
    return b"".join(font.texture.texels[y * font.texture.width + r.u0 : y * font.texture.width + r.u1] for y in range(r.v0, r.v1))


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    base = load(root / "font" / "font_poc_00c7_diagnostics_boundary" / "TEST_REAL_GLYPH_JUE_STYLE_TUNING" / "CANDIDATE_D" / "00c7c9f9.xpr")
    ui = load(root / "font" / "font_poc_00c7_diagnostics_boundary" / "TEST_YAHEI_UI_BOLD_JUE" / "CANDIDATE_YAHEI_UI_BOLD" / "00c7c9f9.xpr")
    items = [(label, extract(base, base.font_data.charmap[cp])) for label, cp in REFS]
    items += [("D", extract(base, 3209)), ("YUI-B", extract(ui, 3209))]
    canvas = Image.new("L", (W * SCALE * len(items), H * SCALE + 25), 0)
    draw = ImageDraw.Draw(canvas)
    nearest = getattr(Image, "Resampling", Image).NEAREST
    for col, (label, data) in enumerate(items):
        x = col * W * SCALE
        crop = Image.frombytes("L", (W, H), data)
        canvas.paste(crop.resize((W * SCALE, H * SCALE), nearest), (x, 0))
        draw.text((x + 2, H * SCALE + 3), label, fill=255)
    out = root / "font" / "font_poc_00c7_diagnostics_boundary" / "TEST_YAHEI_UI_BOLD_JUE" / "yahei_vs_noto_d.png"
    canvas.save(out)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
