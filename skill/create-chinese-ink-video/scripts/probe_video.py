#!/usr/bin/env python3
"""Print compact video metadata as JSON using ffprobe."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    args = parser.parse_args()

    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        parser.error("ffprobe is not available on PATH")

    command = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration,format_name:stream=index,codec_type,codec_name,width,height,r_frame_rate",
        "-of",
        "json",
        str(args.video),
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    print(json.dumps(json.loads(result.stdout), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
