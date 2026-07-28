#!/usr/bin/env python3
"""Build a labeled contact sheet from image files."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", nargs="+", type=Path)
    parser.add_argument("-o", "--output", required=True, type=Path)
    parser.add_argument("--columns", type=int, default=2)
    parser.add_argument("--cell-width", type=int, default=720)
    parser.add_argument("--cell-height", type=int, default=720)
    parser.add_argument("--label-height", type=int, default=48)
    args = parser.parse_args()

    if args.columns < 1:
        parser.error("--columns must be at least 1")
    if args.cell_width < 64 or args.cell_height < 64:
        parser.error("cell dimensions must be at least 64 pixels")

    rows = math.ceil(len(args.images) / args.columns)
    sheet = Image.new(
        "RGB",
        (args.columns * args.cell_width, rows * (args.cell_height + args.label_height)),
        "#171717",
    )
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    for index, path in enumerate(args.images):
        with Image.open(path) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
            image.thumbnail((args.cell_width, args.cell_height), Image.Resampling.LANCZOS)
            x0 = (index % args.columns) * args.cell_width
            y0 = (index // args.columns) * (args.cell_height + args.label_height)
            x = x0 + (args.cell_width - image.width) // 2
            y = y0 + (args.cell_height - image.height) // 2
            sheet.paste(image, (x, y))
            label = f"{index + 1:02d}  {path.name}"
            draw.text((x0 + 12, y0 + args.cell_height + 14), label, fill="white", font=font)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output, quality=92)
    print(f"OK: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
