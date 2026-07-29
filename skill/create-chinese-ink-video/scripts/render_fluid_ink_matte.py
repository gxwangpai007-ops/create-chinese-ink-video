from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import cv2
import numpy as np


def parse_point(value: str) -> tuple[float, float]:
    parts = value.split(",")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("point must be x,y")
    point = (float(parts[0]), float(parts[1]))
    if not all(0.0 <= item <= 1.0 for item in point):
        raise argparse.ArgumentTypeError("point coordinates must be between 0 and 1")
    return point


def splat(
    field: np.ndarray,
    x: float,
    y: float,
    radius_x: float,
    radius_y: float,
    amount: float,
) -> None:
    height, width = field.shape
    x0 = max(0, int(x - radius_x * 3.0))
    x1 = min(width, int(x + radius_x * 3.0) + 1)
    y0 = max(0, int(y - radius_y * 3.0))
    y1 = min(height, int(y + radius_y * 3.0) + 1)
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    blob = np.exp(
        -0.5
        * (
            ((xx - x) / max(radius_x, 0.1)) ** 2
            + ((yy - y) / max(radius_y, 0.1)) ** 2
        )
    )
    field[y0:y1, x0:x1] += blob * amount


def advect(field: np.ndarray, u: np.ndarray, v: np.ndarray, scale: float) -> np.ndarray:
    height, width = field.shape
    yy, xx = np.mgrid[0:height, 0:width].astype(np.float32)
    map_x = np.clip(xx - u * scale, 0.0, width - 1.001)
    map_y = np.clip(yy - v * scale, 0.0, height - 1.001)
    return cv2.remap(
        field,
        map_x,
        map_y,
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REPLICATE,
    )


def add_vortex(
    u: np.ndarray,
    v: np.ndarray,
    x: float,
    y: float,
    radius: float,
    strength: float,
) -> None:
    height, width = u.shape
    x0 = max(0, int(x - radius * 2.4))
    x1 = min(width, int(x + radius * 2.4) + 1)
    y0 = max(0, int(y - radius * 2.4))
    y1 = min(height, int(y + radius * 2.4) + 1)
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    dx = xx - x
    dy = yy - y
    falloff = np.exp(-(dx * dx + dy * dy) / max(2.0 * radius * radius, 0.1))
    u[y0:y1, x0:x1] += -dy / max(radius, 0.1) * falloff * strength
    v[y0:y1, x0:x1] += dx / max(radius, 0.1) * falloff * strength


def project(u: np.ndarray, v: np.ndarray, iterations: int = 12) -> tuple[np.ndarray, np.ndarray]:
    divergence = (
        np.roll(u, -1, axis=1)
        - np.roll(u, 1, axis=1)
        + np.roll(v, -1, axis=0)
        - np.roll(v, 1, axis=0)
    ) * 0.5
    pressure = np.zeros_like(divergence)
    for _ in range(iterations):
        pressure = (
            np.roll(pressure, 1, axis=1)
            + np.roll(pressure, -1, axis=1)
            + np.roll(pressure, 1, axis=0)
            + np.roll(pressure, -1, axis=0)
            - divergence
        ) * 0.25
    u -= (np.roll(pressure, -1, axis=1) - np.roll(pressure, 1, axis=1)) * 0.5
    v -= (np.roll(pressure, -1, axis=0) - np.roll(pressure, 1, axis=0)) * 0.5
    u[:, [0, -1]] = 0.0
    v[[0, -1], :] = 0.0
    return u, v


def confine(u: np.ndarray, v: np.ndarray, strength: float) -> tuple[np.ndarray, np.ndarray]:
    curl = (
        np.roll(v, -1, axis=1)
        - np.roll(v, 1, axis=1)
        - np.roll(u, -1, axis=0)
        + np.roll(u, 1, axis=0)
    ) * 0.5
    magnitude = np.abs(curl)
    gx = (np.roll(magnitude, -1, axis=1) - np.roll(magnitude, 1, axis=1)) * 0.5
    gy = (np.roll(magnitude, -1, axis=0) - np.roll(magnitude, 1, axis=0)) * 0.5
    length = np.sqrt(gx * gx + gy * gy) + 1.0e-5
    u += gy / length * curl * strength
    v -= gx / length * curl * strength
    return u, v


def encoder(path: Path, width: int, height: int, fps: int) -> subprocess.Popen:
    path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "gray",
        "-s",
        f"{width}x{height}",
        "-r",
        str(fps),
        "-i",
        "-",
        "-an",
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
        str(path),
    ]
    return subprocess.Popen(command, stdin=subprocess.PIPE)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render deterministic fluid-ink mattes.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--exposure-output", type=Path, required=True)
    parser.add_argument("--duration", type=float, default=6.4)
    parser.add_argument("--width", type=int, default=540)
    parser.add_argument("--height", type=int, default=960)
    parser.add_argument("--sim-width", type=int, default=150)
    parser.add_argument("--internal-fps", type=int, default=48)
    parser.add_argument("--output-fps", type=int, default=24)
    parser.add_argument("--start", type=parse_point, default=(0.78, 0.72))
    parser.add_argument("--end", type=parse_point, default=(0.74, 0.18))
    parser.add_argument("--inject-until", type=float, default=5.25)
    parser.add_argument("--transport", type=float, default=0.80)
    parser.add_argument("--exposure-rate", type=float, default=0.058)
    args = parser.parse_args()

    if args.internal_fps != args.output_fps * 2:
        raise SystemExit("internal-fps must be exactly twice output-fps")

    sim_w = args.sim_width
    sim_h = int(round(sim_w * args.height / args.width))
    density = np.zeros((sim_h, sim_w), dtype=np.float32)
    exposure = np.zeros_like(density)
    u = np.zeros_like(density)
    v = np.zeros_like(density)
    density_encoder = encoder(args.output.resolve(), args.width, args.height, args.output_fps)
    exposure_encoder = encoder(
        args.exposure_output.resolve(),
        args.width,
        args.height,
        args.output_fps,
    )
    assert density_encoder.stdin is not None
    assert exposure_encoder.stdin is not None

    previous_density: np.ndarray | None = None
    previous_exposure: np.ndarray | None = None
    total_frames = int(round(args.duration * args.internal_fps))
    travel_duration = max(args.inject_until - 0.18, 0.1)

    for frame_index in range(total_frames):
        t = frame_index / args.internal_fps
        progress = np.clip((t - 0.18) / travel_duration, 0.0, 1.0)
        source_x = (args.start[0] + (args.end[0] - args.start[0]) * progress) * sim_w
        source_y = (args.start[1] + (args.end[1] - args.start[1]) * progress) * sim_h

        u = advect(u, u, v, 0.72) * 0.986
        v = advect(v, u, v, 0.72) * 0.986

        if 0.18 <= t <= args.inject_until:
            phase = t * 3.8
            source_x += np.sin(phase) * 2.6 + np.sin(phase * 0.43) * 1.4
            source_y += 4.0
            splat(density, source_x, source_y, 6.4, 8.8, 0.62)
            splat(density, source_x - 6.4, source_y + 7.0, 4.8, 7.2, 0.34)
            splat(density, source_x + 6.2, source_y + 8.0, 5.0, 7.8, 0.30)
            force = np.zeros_like(density)
            splat(force, source_x, source_y + 5.0, 10.0, 14.0, 1.0)
            u += force * (-0.46 + np.sin(phase * 0.71) * 0.18)
            v += force * 0.66
            add_vortex(u, v, source_x - 7.0, source_y + 12.0, 13.0, 0.72 * np.sin(t * 1.34 + 0.30))
            add_vortex(u, v, source_x + 8.0, source_y + 24.0, 17.0, -0.62 * np.sin(t * 1.09 + 2.10))
            add_vortex(u, v, source_x - 13.0, source_y + 34.0, 21.0, 0.40 * np.sin(t * 0.86 + 4.00))

        v += np.clip(density, 0.0, 1.0) * 0.035
        u += np.clip(density, 0.0, 1.0) * -0.024
        u, v = confine(u, v, 0.32)
        u = cv2.GaussianBlur(u, (0, 0), 0.42)
        v = cv2.GaussianBlur(v, (0, 0), 0.42)
        u, v = project(u, v)
        density = advect(density, u, v, args.transport)
        density = cv2.GaussianBlur(density, (0, 0), 0.32) * 0.998
        density = np.clip(density, 0.0, 1.5)
        exposure += np.clip(density - 0.025, 0.0, 1.0) * args.exposure_rate
        exposure = np.maximum(exposure, cv2.GaussianBlur(exposure, (0, 0), 1.35) * 0.998)
        exposure = np.clip(exposure, 0.0, 1.0)

        visible = np.sqrt(np.clip(density, 0.0, 1.0))
        visible = cv2.resize(visible, (args.width, args.height), interpolation=cv2.INTER_CUBIC)
        reached = cv2.resize(exposure, (args.width, args.height), interpolation=cv2.INTER_CUBIC)
        visible_u8 = np.clip(visible * 255.0, 0.0, 255.0).astype(np.uint8)
        reached_u8 = np.clip(reached * 255.0, 0.0, 255.0).astype(np.uint8)

        if frame_index % 2 == 1:
            assert previous_density is not None and previous_exposure is not None
            blended_density = cv2.addWeighted(previous_density, 0.5, visible_u8, 0.5, 0.0)
            blended_exposure = cv2.addWeighted(previous_exposure, 0.5, reached_u8, 0.5, 0.0)
            density_encoder.stdin.write(blended_density.tobytes())
            exposure_encoder.stdin.write(blended_exposure.tobytes())
        previous_density = visible_u8
        previous_exposure = reached_u8

    density_encoder.stdin.close()
    exposure_encoder.stdin.close()
    density_code = density_encoder.wait()
    exposure_code = exposure_encoder.wait()
    if density_code or exposure_code:
        raise SystemExit(density_code or exposure_code)

    manifest = {
        "duration": args.duration,
        "resolution": [args.width, args.height],
        "simulation_resolution": [sim_w, sim_h],
        "internal_fps": args.internal_fps,
        "output_fps": args.output_fps,
        "start": args.start,
        "end": args.end,
        "inject_until": args.inject_until,
        "transport": args.transport,
        "exposure_rate": args.exposure_rate,
        "density_output": str(args.output.resolve()),
        "exposure_output": str(args.exposure_output.resolve()),
    }
    args.output.with_suffix(".json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
