from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import cv2
import numpy as np


DEFAULT_BLOOMS = [
    {
        "center": [0.24, 0.72],
        "start": 0.20,
        "duration": 1.55,
        "radius": [0.22, 0.17],
        "gap_angle": 0.25,
        "phase": 0.70,
    },
    {
        "center": [0.53, 0.58],
        "start": 0.70,
        "duration": 1.85,
        "radius": [0.25, 0.22],
        "gap_angle": 2.55,
        "phase": 2.10,
    },
    {
        "center": [0.68, 0.38],
        "start": 1.20,
        "duration": 1.75,
        "radius": [0.20, 0.20],
        "gap_angle": -0.80,
        "phase": 4.00,
    },
    {
        "center": [0.42, 0.30],
        "start": 1.75,
        "duration": 1.60,
        "radius": [0.18, 0.16],
        "gap_angle": 1.50,
        "phase": 5.20,
    },
]


def smoothstep(value: np.ndarray | float) -> np.ndarray | float:
    clipped = np.clip(value, 0.0, 1.0)
    return clipped * clipped * (3.0 - 2.0 * clipped)


def normalize(field: np.ndarray) -> np.ndarray:
    low, high = np.percentile(field, [2.0, 98.0])
    return np.clip((field - low) / max(high - low, 1.0e-6), 0.0, 1.0)


def build_texture(height: int, width: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    fine = rng.normal(0.0, 1.0, (height, width)).astype(np.float32)
    horizontal = cv2.GaussianBlur(fine, (25, 3), 0)
    vertical = cv2.GaussianBlur(fine, (5, 23), 0)
    coarse_small = rng.normal(0.0, 1.0, (max(2, height // 14), max(2, width // 14)))
    coarse = cv2.resize(
        coarse_small.astype(np.float32),
        (width, height),
        interpolation=cv2.INTER_CUBIC,
    )
    return np.clip(
        normalize(horizontal) * 0.40
        + normalize(vertical) * 0.32
        + normalize(coarse) * 0.28,
        0.0,
        1.0,
    )


def load_blooms(path: Path | None) -> list[dict[str, object]]:
    if path is None:
        return DEFAULT_BLOOMS
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError("--blooms-json must contain a non-empty JSON array")
    required = {"center", "start", "duration", "radius", "gap_angle", "phase"}
    for index, bloom in enumerate(data):
        if not isinstance(bloom, dict) or not required.issubset(bloom):
            raise ValueError(f"Bloom {index} is missing required keys: {sorted(required)}")
    return data


def calculate_fields(
    t: float,
    nx: np.ndarray,
    ny: np.ndarray,
    texture: np.ndarray,
    blooms: list[dict[str, object]],
) -> tuple[np.ndarray, np.ndarray]:
    exposure = np.zeros_like(texture)
    density = np.zeros_like(texture)
    for bloom in blooms:
        center_x, center_y = [float(value) for value in bloom["center"]]
        radius_x, radius_y = [float(value) for value in bloom["radius"]]
        start = float(bloom["start"])
        duration = float(bloom["duration"])
        gap_angle = float(bloom["gap_angle"])
        phase = float(bloom["phase"])

        raw = np.clip((t - start) / max(duration, 1.0e-4), 0.0, 1.0)
        if raw <= 0.0:
            continue
        progress = float(smoothstep(raw))
        dx = (nx - center_x) / max(radius_x, 1.0e-4)
        dy = (ny - center_y) / max(radius_y, 1.0e-4)
        distance = np.sqrt(dx * dx + dy * dy)
        angle = np.arctan2(dy, dx)
        angle_delta = np.arctan2(
            np.sin(angle - gap_angle),
            np.cos(angle - gap_angle),
        )

        current_radius = 0.10 + progress * 1.02
        irregularity = (
            (texture - 0.5) * 0.18
            + np.sin(angle * 3.0 + phase) * 0.045
            + np.sin(angle * 5.0 - phase * 0.7) * 0.022
        )
        signed = current_radius + irregularity - distance
        gap_width = max(0.20, 0.44 + 0.14 * np.sin(phase))
        gap = np.exp(-0.5 * np.square(angle_delta / gap_width))
        close_progress = float(smoothstep((progress - 0.58) / 0.40))
        c_shape = np.clip(1.0 - gap * 0.90 * (1.0 - close_progress), 0.0, 1.0)

        body = smoothstep(signed / 0.085) * c_shape
        ring = np.exp(-np.square(signed / 0.070))
        fibres = ring * c_shape * (0.24 + texture * 0.96)
        exposure = np.maximum(exposure, body)
        density = np.maximum(density, fibres)
    return np.clip(density, 0.0, 1.0), np.clip(exposure, 0.0, 1.0)


def start_encoder(
    output: Path,
    width: int,
    height: int,
    internal_fps: int,
    output_fps: int,
) -> subprocess.Popen[bytes]:
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{width}x{height}",
        "-r",
        str(internal_fps),
        "-i",
        "-",
        "-vf",
        (
            "tmix=frames=2:weights='1 1',"
            f"select='not(mod(n,2))',setpts=N/({output_fps}*TB)"
        ),
        "-an",
        "-r",
        str(output_fps),
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output),
    ]
    return subprocess.Popen(command, stdin=subprocess.PIPE)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--exposure-output", type=Path, required=True)
    parser.add_argument("--mask", type=Path)
    parser.add_argument("--blooms-json", type=Path)
    parser.add_argument("--duration", type=float, default=4.8)
    parser.add_argument("--width", type=int, default=540)
    parser.add_argument("--height", type=int, default=960)
    parser.add_argument("--internal-fps", type=int, default=48)
    parser.add_argument("--output-fps", type=int, default=24)
    parser.add_argument("--seed", type=int, default=4177)
    args = parser.parse_args()

    output = args.output.resolve()
    exposure_output = args.exposure_output.resolve()
    blooms = load_blooms(args.blooms_json.resolve() if args.blooms_json else None)

    yy, xx = np.mgrid[0 : args.height, 0 : args.width].astype(np.float32)
    nx = xx / max(args.width - 1, 1)
    ny = yy / max(args.height - 1, 1)
    texture = build_texture(args.height, args.width, args.seed)

    if args.mask:
        mask = cv2.imread(str(args.mask.resolve()), cv2.IMREAD_GRAYSCALE)
        if mask is None:
            raise SystemExit(f"Cannot read mask: {args.mask}")
        mask = cv2.resize(mask, (args.width, args.height), interpolation=cv2.INTER_AREA)
        mask = mask.astype(np.float32) / 255.0
    else:
        mask = np.ones((args.height, args.width), dtype=np.float32)

    density_encoder = start_encoder(
        output,
        args.width,
        args.height,
        args.internal_fps,
        args.output_fps,
    )
    exposure_encoder = start_encoder(
        exposure_output,
        args.width,
        args.height,
        args.internal_fps,
        args.output_fps,
    )
    assert density_encoder.stdin is not None
    assert exposure_encoder.stdin is not None

    total_frames = int(round(args.duration * args.internal_fps))
    for frame_index in range(total_frames):
        t = frame_index / args.internal_fps
        density, exposure = calculate_fields(t, nx, ny, texture, blooms)
        density *= cv2.dilate(mask, np.ones((7, 7), np.uint8))
        exposure *= mask
        density_rgb = np.repeat((density * 255.0).astype(np.uint8)[..., None], 3, axis=2)
        exposure_rgb = np.repeat(
            (exposure * 255.0).astype(np.uint8)[..., None],
            3,
            axis=2,
        )
        density_encoder.stdin.write(density_rgb.tobytes())
        exposure_encoder.stdin.write(exposure_rgb.tobytes())

    density_encoder.stdin.close()
    exposure_encoder.stdin.close()
    density_code = density_encoder.wait()
    exposure_code = exposure_encoder.wait()
    if density_code != 0 or exposure_code != 0:
        raise SystemExit(max(density_code, exposure_code))

    manifest = {
        "density_output": str(output),
        "exposure_output": str(exposure_output),
        "duration": args.duration,
        "resolution": [args.width, args.height],
        "internal_fps": args.internal_fps,
        "output_fps": args.output_fps,
        "seed": args.seed,
        "mask": str(args.mask.resolve()) if args.mask else None,
        "blooms": blooms,
        "coordinates": "normalized 0-1",
    }
    output.with_suffix(".json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(output)
    print(exposure_output)


if __name__ == "__main__":
    main()
