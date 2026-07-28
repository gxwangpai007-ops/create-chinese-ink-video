#!/usr/bin/env python3
"""Measure consecutive-frame luminance change and report suspicious timestamps."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path


def percentile(values: list[float], percent: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * percent / 100.0
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def read_exact(stream: object, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining:
        chunk = stream.read(remaining)  # type: ignore[attr-defined]
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def probe_fps(video: Path, ffprobe: str) -> float:
    command = [
        ffprobe,
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=avg_frame_rate",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video),
    ]
    value = subprocess.run(command, check=True, capture_output=True, text=True).stdout.strip()
    fps = float(Fraction(value))
    if fps <= 0:
        raise ValueError("video frame rate must be positive")
    return fps


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--sample-width", type=int, default=96)
    parser.add_argument("--sample-height", type=int, default=96)
    parser.add_argument("--near-static", type=float, default=0.5)
    parser.add_argument("--large-change", type=float, default=4.0)
    parser.add_argument("--top", type=int, default=12)
    parser.add_argument("--fail-peak", type=float)
    args = parser.parse_args()

    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if ffmpeg is None or ffprobe is None:
        parser.error("ffmpeg and ffprobe must be available on PATH")
    if args.sample_width < 16 or args.sample_height < 16:
        parser.error("sample dimensions must be at least 16 pixels")

    fps = probe_fps(args.video, ffprobe)
    frame_size = args.sample_width * args.sample_height
    command = [
        ffmpeg,
        "-v",
        "error",
        "-i",
        str(args.video),
        "-an",
        "-vf",
        f"scale={args.sample_width}:{args.sample_height},format=gray",
        "-f",
        "rawvideo",
        "pipe:1",
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert process.stdout is not None
    previous: bytes | None = None
    deltas: list[float] = []
    frame_count = 0

    while True:
        frame = read_exact(process.stdout, frame_size)
        if not frame:
            break
        if len(frame) != frame_size:
            process.kill()
            raise RuntimeError("ffmpeg produced a partial raw frame")
        if previous is not None:
            total = sum(abs(current - prior) for current, prior in zip(frame, previous))
            deltas.append(total / frame_size)
        previous = frame
        frame_count += 1

    stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
    if process.wait() != 0:
        raise RuntimeError(f"ffmpeg failed: {stderr.strip()}")
    if frame_count < 2:
        raise ValueError("video must contain at least two frames")

    ranked = sorted(enumerate(deltas), key=lambda item: item[1], reverse=True)[: args.top]
    report = {
        "video": str(args.video),
        "fps": round(fps, 6),
        "frames": frame_count,
        "pairs": len(deltas),
        "sample_size": [args.sample_width, args.sample_height],
        "near_static_lt": args.near_static,
        "near_static_pairs": sum(value < args.near_static for value in deltas),
        "large_change_gt": args.large_change,
        "large_change_pairs": sum(value > args.large_change for value in deltas),
        "mean": round(sum(deltas) / len(deltas), 3),
        "p95": round(percentile(deltas, 95), 3),
        "peak": round(max(deltas), 3),
        "top_peaks": [
            {
                "frame": index + 1,
                "time": round((index + 1) / fps, 3),
                "delta": round(value, 3),
            }
            for index, value in ranked
        ],
    }
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    if args.fail_peak is not None and report["peak"] > args.fail_peak:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
