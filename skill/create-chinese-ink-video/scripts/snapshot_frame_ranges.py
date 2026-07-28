#!/usr/bin/env python3
"""Capture resumable HyperFrames frame ranges and optionally merge them into a sequence."""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
from pathlib import Path


FRAME_RE = re.compile(r"^frame-(\d+)-")


def parse_ranges(value: str, fps: float) -> list[int]:
    indices: set[int] = set()
    for item in value.split(","):
        token = item.strip()
        if not token:
            continue
        parts = token.split("-", 1)
        if len(parts) != 2:
            raise ValueError(f"invalid range: {token}")
        start, end = (float(part.strip()) for part in parts)
        if start < 0 or end <= start:
            raise ValueError(f"range must satisfy 0 <= start < end: {token}")
        first = math.floor(start * fps)
        last = math.ceil(end * fps) - 1
        indices.update(range(first, last + 1))
    if not indices:
        raise ValueError("--ranges did not produce any frames")
    return sorted(indices)


def contiguous_batches(indices: list[int], batch_size: int) -> list[list[int]]:
    groups: list[list[int]] = []
    current: list[int] = []
    previous: int | None = None
    for index in indices:
        if current and (index != previous + 1 or len(current) >= batch_size):
            groups.append(current)
            current = []
        current.append(index)
        previous = index
    if current:
        groups.append(current)
    return groups


def pinned_version(project: Path) -> str:
    package_json = project / "package.json"
    if package_json.exists():
        match = re.search(r"hyperframes@([0-9]+(?:\.[0-9]+){1,2})", package_json.read_text(encoding="utf-8"))
        if match:
            return match.group(1)
    return "latest"


def local_frames(directory: Path) -> list[Path]:
    frames = []
    for path in directory.glob("frame-*.png"):
        match = FRAME_RE.match(path.name)
        if match:
            frames.append((int(match.group(1)), path))
    return [path for _, path in sorted(frames)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--ranges", required=True, help="Comma-separated second ranges, e.g. 3.1-3.9,7-7.8")
    parser.add_argument("--fps", type=float, default=48.0)
    parser.add_argument("--batch-size", type=int, default=60)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--sequence-dir", type=Path)
    parser.add_argument("--hyperframes-version")
    parser.add_argument("--timeout", type=int, default=30000)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    if args.fps <= 0 or args.batch_size < 1:
        parser.error("--fps and --batch-size must be positive")
    try:
        indices = parse_ranges(args.ranges, args.fps)
    except ValueError as error:
        parser.error(str(error))

    batches = contiguous_batches(indices, args.batch_size)
    version = args.hyperframes_version or pinned_version(args.project)
    plan = {
        "project": str(args.project.resolve()),
        "fps": args.fps,
        "frame_count": len(indices),
        "first_frame": indices[0],
        "last_frame": indices[-1],
        "hyperframes_version": version,
        "batches": [
            {
                "start_frame": batch[0],
                "end_frame": batch[-1],
                "count": len(batch),
                "start_time": round(batch[0] / args.fps, 6),
                "end_time": round(batch[-1] / args.fps, 6),
            }
            for batch in batches
        ],
    }
    if args.dry_run:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0

    npx = shutil.which("npx.cmd") or shutil.which("npx")
    if npx is None:
        parser.error("npx is not available on PATH")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.sequence_dir:
        args.sequence_dir.mkdir(parents=True, exist_ok=True)

    mapped: list[dict[str, object]] = []
    for batch in batches:
        batch_dir = args.output_dir / f"range-{batch[0]:06d}-{batch[-1]:06d}"
        frames = local_frames(batch_dir) if batch_dir.exists() else []
        if len(frames) != len(batch):
            times = ",".join(f"{index / args.fps:.6f}" for index in batch)
            command = [
                npx,
                "--yes",
                f"hyperframes@{version}",
                "snapshot",
                str(args.project.resolve()),
                "--at",
                times,
                "--no-end",
                "--output",
                str(batch_dir.resolve()),
                "--describe",
                "false",
                "--timeout",
                str(args.timeout),
            ]
            subprocess.run(command, check=True)
            frames = local_frames(batch_dir)
        if len(frames) != len(batch):
            raise RuntimeError(
                f"{batch_dir} contains {len(frames)} frames; expected {len(batch)}"
            )

        for global_index, source in zip(batch, frames):
            destination: Path | None = None
            if args.sequence_dir:
                destination = args.sequence_dir / f"frame-{global_index:06d}.png"
                if destination.exists() and not args.overwrite:
                    raise FileExistsError(f"refusing to overwrite {destination}")
                shutil.copy2(source, destination)
            mapped.append(
                {
                    "global_frame": global_index,
                    "time": round(global_index / args.fps, 6),
                    "source": str(source),
                    "destination": str(destination) if destination else None,
                }
            )

    report = {**plan, "mapped_frames": mapped}
    index_path = args.output_dir / "snapshot-frame-ranges-index.json"
    index_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK: {index_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
