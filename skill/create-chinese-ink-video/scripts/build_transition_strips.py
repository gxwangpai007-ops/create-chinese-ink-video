#!/usr/bin/env python3
"""Build labeled before/during/after frame strips around video transitions."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


def parse_times(value: str) -> list[float]:
    times = [float(item.strip()) for item in value.split(",") if item.strip()]
    if not times or any(item < 0 for item in times):
        raise ValueError("--transitions must contain non-negative seconds")
    return times


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--transitions", required=True, help="Comma-separated cut times in seconds")
    parser.add_argument("-o", "--output", required=True, type=Path)
    parser.add_argument("--window", type=float, default=0.8)
    parser.add_argument("--samples", type=int, default=7)
    parser.add_argument("--cell-width", type=int, default=180)
    parser.add_argument("--cell-height", type=int, default=320)
    parser.add_argument("--label-height", type=int, default=34)
    args = parser.parse_args()

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        parser.error("ffmpeg is not available on PATH")
    if args.samples < 3 or args.window <= 0:
        parser.error("--samples must be at least 3 and --window must be positive")

    try:
        transitions = parse_times(args.transitions)
    except ValueError as error:
        parser.error(str(error))

    width = args.samples * args.cell_width
    row_height = args.cell_height + args.label_height
    sheet = Image.new("RGB", (width, len(transitions) * row_height), "#e8dfcd")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    with tempfile.TemporaryDirectory(prefix="ink-transition-") as temp:
        temp_dir = Path(temp)
        for row, transition in enumerate(transitions):
            for column in range(args.samples):
                fraction = column / (args.samples - 1)
                offset = -args.window + 2 * args.window * fraction
                timestamp = max(0.0, transition + offset)
                frame_path = temp_dir / f"r{row:02d}-c{column:02d}.jpg"
                command = [
                    ffmpeg,
                    "-y",
                    "-v",
                    "error",
                    "-ss",
                    f"{timestamp:.6f}",
                    "-i",
                    str(args.video),
                    "-frames:v",
                    "1",
                    "-q:v",
                    "2",
                    str(frame_path),
                ]
                subprocess.run(command, check=True)
                with Image.open(frame_path) as source:
                    frame = ImageOps.contain(
                        ImageOps.exif_transpose(source).convert("RGB"),
                        (args.cell_width, args.cell_height),
                        Image.Resampling.LANCZOS,
                    )
                    x0 = column * args.cell_width
                    y0 = row * row_height
                    x = x0 + (args.cell_width - frame.width) // 2
                    y = y0 + (args.cell_height - frame.height) // 2
                    sheet.paste(frame, (x, y))
                    label = f"{timestamp:.2f}s ({offset:+.2f})"
                    draw.text((x0 + 6, y0 + args.cell_height + 10), label, fill="#171717", font=font)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output, quality=92)
    print(f"OK: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
