#!/usr/bin/env python3
"""Extract proof frames from a video at explicit timestamps using ffmpeg."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--times", required=True, help="Comma-separated timestamps in seconds")
    parser.add_argument("-o", "--output-dir", required=True, type=Path)
    args = parser.parse_args()

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        parser.error("ffmpeg is not available on PATH")
    times = [float(value.strip()) for value in args.times.split(",") if value.strip()]
    if not times or any(value < 0 for value in times):
        parser.error("--times must contain non-negative timestamps")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for index, timestamp in enumerate(times, start=1):
        output = args.output_dir / f"proof-{index:02d}-{timestamp:.2f}s.jpg"
        command = [
            ffmpeg,
            "-y",
            "-ss",
            f"{timestamp:.3f}",
            "-i",
            str(args.video),
            "-frames:v",
            "1",
            "-q:v",
            "2",
            str(output),
        ]
        subprocess.run(command, check=True, capture_output=True)
        print(f"OK: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
