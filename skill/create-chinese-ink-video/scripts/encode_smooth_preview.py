#!/usr/bin/env python3
"""Encode a 48 fps deterministic frame sequence into a smooth 24 fps H.264 proof."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, text=True, capture_output=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("frames_dir", type=Path)
    parser.add_argument("-o", "--output", required=True, type=Path)
    parser.add_argument("--pattern", default="frame-%06d.png")
    parser.add_argument("--internal-fps", type=float, default=48.0)
    parser.add_argument("--output-fps", type=float, default=24.0)
    parser.add_argument("--mix-frames", type=int, default=2)
    parser.add_argument("--crf", type=int, default=20)
    parser.add_argument("--preset", default="medium")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    if args.internal_fps <= 0 or args.output_fps <= 0:
        parser.error("frame rates must be positive")
    if args.mix_frames < 1:
        parser.error("--mix-frames must be at least 1")

    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        parser.error("ffmpeg and ffprobe must be available on PATH")

    frames = sorted(args.frames_dir.glob("frame-*.png"))
    if not frames:
        parser.error(f"no frame-*.png files found in {args.frames_dir}")
    expected = list(range(len(frames)))
    actual = []
    for path in frames:
        try:
            actual.append(int(path.stem.split("-")[-1]))
        except ValueError:
            parser.error(f"cannot parse frame index from {path.name}")
    if actual != expected:
        parser.error("frame sequence is not contiguous from frame-000000.png")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    weights = " ".join("1" for _ in range(args.mix_frames))
    filters = (
        f"tmix=frames={args.mix_frames}:weights='{weights}',"
        f"fps={args.output_fps},format=yuv420p"
    )
    command = [
        ffmpeg,
        "-y",
        "-framerate",
        str(args.internal_fps),
        "-i",
        str(args.frames_dir / args.pattern),
        "-vf",
        filters,
        "-c:v",
        "libx264",
        "-preset",
        args.preset,
        "-crf",
        str(args.crf),
        "-movflags",
        "+faststart",
        str(args.output),
    ]
    run(command)
    run([ffmpeg, "-v", "error", "-i", str(args.output), "-f", "null", "-"])
    probe = run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "stream=codec_name,width,height,r_frame_rate,nb_frames",
            "-show_entries",
            "format=duration,size",
            "-of",
            "json",
            str(args.output),
        ]
    )
    metadata = json.loads(probe.stdout)
    report = {
        "output": str(args.output.resolve()),
        "source_frames": len(frames),
        "internal_fps": args.internal_fps,
        "output_fps": args.output_fps,
        "mix_frames": args.mix_frames,
        "decode_scan": "passed",
        "probe": metadata,
    }
    report_path = args.report or args.output.with_suffix(".json")
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
