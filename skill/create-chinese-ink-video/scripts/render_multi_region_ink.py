from __future__ import annotations

import argparse
import json
import math
import subprocess
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image


def smoothstep(value: np.ndarray | float) -> np.ndarray | float:
    value = np.clip(value, 0.0, 1.0)
    return value * value * (3.0 - 2.0 * value)


def normalize(field: np.ndarray) -> np.ndarray:
    low, high = np.percentile(field, [2.0, 98.0])
    return np.clip((field - low) / max(high - low, 1.0e-6), 0.0, 1.0)


def texture(height: int, width: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    fine = rng.normal(0.0, 1.0, (height, width)).astype(np.float32)
    horizontal = cv2.GaussianBlur(fine, (27, 3), 0)
    vertical = cv2.GaussianBlur(fine, (5, 25), 0)
    small = rng.normal(
        0.0,
        1.0,
        (max(2, height // 15), max(2, width // 15)),
    ).astype(np.float32)
    coarse = cv2.resize(small, (width, height), interpolation=cv2.INTER_CUBIC)
    return np.clip(
        normalize(horizontal) * 0.38
        + normalize(vertical) * 0.32
        + normalize(coarse) * 0.30,
        0.0,
        1.0,
    )


def load_rgb(path: Path, size: tuple[int, int]) -> np.ndarray:
    return np.asarray(
        Image.open(path).convert("RGB").resize(size, Image.Resampling.LANCZOS),
        dtype=np.float32,
    )


def load_mask(path: Path, size: tuple[int, int]) -> np.ndarray:
    return np.asarray(
        Image.open(path).convert("L").resize(size, Image.Resampling.LANCZOS),
        dtype=np.float32,
    ) / 255.0


def check_unit(value: float, label: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{label} must be between 0 and 1")


def validate_config(config: dict[str, Any]) -> None:
    if not isinstance(config.get("environment_paths"), list):
        raise ValueError("environment_paths must be a list")
    if not config["environment_paths"]:
        raise ValueError("environment_paths must contain at least one path")
    if not isinstance(config.get("regions"), list):
        raise ValueError("regions must be a list")
    if not config["regions"]:
        raise ValueError("regions must contain at least one region")

    names: set[str] = set()
    for path_index, path in enumerate(config["environment_paths"]):
        points = path.get("points")
        if not isinstance(points, list) or len(points) < 2:
            raise ValueError(
                f"environment_paths[{path_index}].points needs at least two points"
            )
        for point_index, point in enumerate(points):
            if not isinstance(point, list) or len(point) != 3:
                raise ValueError(
                    f"environment path point {point_index} must be [x, y, time]"
                )
            check_unit(float(point[0]), "path x")
            check_unit(float(point[1]), "path y")
            if float(point[2]) < 0.0:
                raise ValueError("path time must be non-negative")

    for region_index, region in enumerate(config["regions"]):
        name = str(region.get("name", "")).strip()
        if not name:
            raise ValueError(f"regions[{region_index}].name is required")
        if name in names:
            raise ValueError(f"duplicate region name: {name}")
        names.add(name)
        zone = region.get("zone", {})
        for key in ("cx", "cy", "rx", "ry"):
            if key not in zone:
                raise ValueError(f"region {name} zone.{key} is required")
        check_unit(float(zone["cx"]), f"{name} zone.cx")
        check_unit(float(zone["cy"]), f"{name} zone.cy")
        if float(zone["rx"]) <= 0.0 or float(zone["ry"]) <= 0.0:
            raise ValueError(f"region {name} radii must be positive")
        blooms = region.get("blooms")
        if not isinstance(blooms, list) or not blooms:
            raise ValueError(f"region {name} needs at least one bloom")
        for bloom_index, bloom in enumerate(blooms):
            for key in ("cx", "cy", "start", "duration", "rx", "ry"):
                if key not in bloom:
                    raise ValueError(
                        f"region {name} bloom {bloom_index}.{key} is required"
                    )
            check_unit(float(bloom["cx"]), f"{name} bloom.cx")
            check_unit(float(bloom["cy"]), f"{name} bloom.cy")
            if float(bloom["duration"]) <= 0.0:
                raise ValueError(f"region {name} bloom duration must be positive")


def sample_path(
    points: list[list[float]],
    samples_per_segment: int,
) -> list[tuple[float, float, float]]:
    result: list[tuple[float, float, float]] = []
    for start, end in zip(points[:-1], points[1:]):
        for progress in np.linspace(
            0.0,
            1.0,
            samples_per_segment,
            endpoint=False,
        ):
            result.append(
                (
                    float(start[0] + (end[0] - start[0]) * progress),
                    float(start[1] + (end[1] - start[1]) * progress),
                    float(start[2] + (end[2] - start[2]) * progress),
                )
            )
    end = points[-1]
    result.append((float(end[0]), float(end[1]), float(end[2])))
    return result


def environment_arrival(
    nx: np.ndarray,
    ny: np.ndarray,
    noise: np.ndarray,
    config: dict[str, Any],
) -> np.ndarray:
    arrival = np.full_like(nx, 999.0, dtype=np.float32)
    for path in config["environment_paths"]:
        spread = path.get("spread", [0.42, 0.27])
        spread_x = max(float(spread[0]), 1.0e-5)
        spread_y = max(float(spread[1]), 1.0e-5)
        travel_rate = float(path.get("travel_rate", 1.28))
        samples = int(path.get("samples_per_segment", 15))
        for px, py, point_time in sample_path(path["points"], samples):
            distance = np.sqrt(
                np.square((nx - px) / spread_x)
                + np.square((ny - py) / spread_y)
            )
            candidate = point_time + distance * travel_rate
            arrival = np.minimum(arrival, candidate.astype(np.float32))
    noise_seconds = float(config.get("environment", {}).get("noise_seconds", 0.30))
    return arrival + (noise - 0.5) * noise_seconds


def ellipse_zone(
    nx: np.ndarray,
    ny: np.ndarray,
    zone_config: dict[str, Any],
) -> np.ndarray:
    ellipse = np.sqrt(
        np.square((nx - float(zone_config["cx"])) / float(zone_config["rx"]))
        + np.square((ny - float(zone_config["cy"])) / float(zone_config["ry"]))
    )
    edge = max(float(zone_config.get("edge", 0.18)), 1.0e-5)
    return smoothstep((1.08 - ellipse) / edge).astype(np.float32)


def region_arrival(
    nx: np.ndarray,
    ny: np.ndarray,
    fibres: np.ndarray,
    region: dict[str, Any],
) -> tuple[np.ndarray, np.ndarray]:
    arrival = np.full_like(nx, 999.0, dtype=np.float32)
    for bloom in region["blooms"]:
        rx = max(float(bloom["rx"]), 1.0e-5)
        ry = max(float(bloom["ry"]), 1.0e-5)
        dx = (nx - float(bloom["cx"])) / rx
        dy = (ny - float(bloom["cy"])) / ry
        distance = np.sqrt(dx * dx + dy * dy)
        angle = np.arctan2(dy, dx)
        gap_angle = float(bloom.get("gap_angle", 0.0))
        phase = float(bloom.get("phase", 0.0))
        angle_delta = np.arctan2(
            np.sin(angle - gap_angle),
            np.cos(angle - gap_angle),
        )
        gap_width = max(float(bloom.get("gap_width", 0.45)), 0.12)
        gap_delay = (
            np.exp(-0.5 * np.square(angle_delta / gap_width))
            * float(bloom.get("gap_delay", 0.38))
        )
        irregularity = (
            (fibres - 0.5) * float(bloom.get("fibre_strength", 0.18))
            + np.sin(angle * 3.0 + phase) * 0.050
            + np.sin(angle * 5.0 - phase * 0.7) * 0.024
        )
        radial = np.clip((distance - irregularity - 0.08) / 1.02, 0.0, 1.25)
        candidate = (
            float(bloom["start"])
            + float(bloom["duration"]) * radial
            + gap_delay
        )
        arrival = np.minimum(arrival, candidate.astype(np.float32))
    return arrival, ellipse_zone(nx, ny, region["zone"])


def negative_space_keep(
    nx: np.ndarray,
    ny: np.ndarray,
    config: dict[str, Any],
    config_dir: Path,
    size: tuple[int, int],
) -> np.ndarray:
    keep = np.ones_like(nx, dtype=np.float32)
    for item in config.get("negative_space", []):
        strength = float(item.get("strength", 1.0))
        if "mask" in item:
            mask_path = (config_dir / item["mask"]).resolve()
            zone = load_mask(mask_path, size)
        else:
            zone = ellipse_zone(nx, ny, item)
        keep *= 1.0 - np.clip(zone * strength, 0.0, 1.0)
    return np.clip(keep, 0.0, 1.0)


def camera_breath(
    frame: np.ndarray,
    time_sec: float,
    duration: float,
    config: dict[str, Any],
) -> np.ndarray:
    amount = float(config.get("amount", 0.0))
    if amount <= 0.0:
        return frame
    phase = 0.5 - 0.5 * math.cos(
        math.pi * float(np.clip(time_sec / duration, 0.0, 1.0))
    )
    scale = 1.0 + phase * amount
    height, width = frame.shape[:2]
    crop_w = max(2, int(round(width / scale)))
    crop_h = max(2, int(round(height / scale)))
    center = config.get("center", [0.5, 0.5])
    center_x = width * float(center[0])
    center_y = height * float(center[1])
    left = max(0, min(width - crop_w, int(round(center_x - crop_w / 2))))
    top = max(0, min(height - crop_h, int(round(center_y - crop_h / 2))))
    crop = frame[top : top + crop_h, left : left + crop_w]
    return cv2.resize(crop, (width, height), interpolation=cv2.INTER_LANCZOS4)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render a config-driven multi-region Chinese ink formation video."
    )
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--clean", type=Path, required=True)
    parser.add_argument("--paper", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--duration", type=float)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    config_path = args.config.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    validate_config(config)
    if args.validate_only:
        print(f"valid: {config_path}")
        return
    if args.output is None:
        parser.error("--output is required unless --validate-only is used")

    output_config = config.get("output", {})
    width = int(args.width or output_config.get("width", 540))
    height = int(args.height or output_config.get("height", 960))
    duration = float(args.duration or output_config.get("duration", 8.0))
    internal_fps = int(output_config.get("internal_fps", 48))
    output_fps = int(output_config.get("output_fps", 24))
    crf = int(output_config.get("crf", 21))
    if internal_fps != output_fps * 2:
        raise ValueError("internal_fps must equal output_fps * 2")
    if width <= 0 or height <= 0 or duration <= 0.0:
        raise ValueError("width, height, and duration must be positive")

    size = (width, height)
    master = load_rgb(args.master, size)
    clean = load_rgb(args.clean, size)
    paper = load_rgb(args.paper, size)
    yy, xx = np.mgrid[0:height, 0:width].astype(np.float32)
    nx = xx / max(width - 1, 1)
    ny = yy / max(height - 1, 1)
    seed = int(config.get("seed", 8177))
    env_texture = texture(height, width, seed + 35844)
    fibre_texture = texture(height, width, seed)
    env_arrival = environment_arrival(nx, ny, env_texture, config)
    env_strength = np.clip(
        np.mean(np.abs(clean - paper), axis=2)
        / float(config.get("environment", {}).get("strength_scale", 72.0)),
        0.0,
        1.0,
    )
    keep = negative_space_keep(nx, ny, config, config_path.parent, size)
    region_fields = [
        (*region_arrival(nx, ny, fibre_texture, region), region)
        for region in config["regions"]
    ]

    difference = np.mean(np.abs(master - clean), axis=2)
    lock_masks: dict[str, np.ndarray] = {}
    for _arrival, zone, region in region_fields:
        lock_config = region.get("lock", {})
        if "mask" in lock_config:
            mask_path = (config_path.parent / lock_config["mask"]).resolve()
            mask = load_mask(mask_path, size)
        else:
            threshold = float(lock_config.get("threshold", 12.0))
            softness = max(float(lock_config.get("softness", 44.0)), 1.0e-5)
            mask = smoothstep((difference - threshold) / softness).astype(np.float32)
        lock_masks[region["name"]] = np.clip(mask * zone, 0.0, 1.0)

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
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
        str(crf),
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    assert process.stdin is not None

    environment = config.get("environment", {})
    env_softness = float(environment.get("reveal_softness", 0.38))
    env_front_width = float(environment.get("front_width", 0.16))
    env_front_opacity = float(environment.get("front_opacity", 0.17))
    wet_rgb = np.asarray(
        environment.get("wet_rgb", [42.0, 46.0, 45.0]),
        dtype=np.float32,
    )
    settle = config.get("settle", {})
    settle_start = float(settle.get("start", duration * 0.85))
    settle_duration = max(float(settle.get("duration", duration * 0.14)), 1.0e-5)
    settle_reduction = float(settle.get("front_reduction", 0.62))

    total_frames = int(round(duration * internal_fps))
    for frame_index in range(total_frames):
        time_sec = frame_index / internal_fps
        env_reveal = smoothstep(
            (time_sec - env_arrival) / max(env_softness, 1.0e-5)
        ).astype(np.float32)
        env_alpha = env_reveal * (0.30 + env_strength * 0.70) * keep
        frame = paper * (1.0 - env_alpha[..., None]) + clean * env_alpha[..., None]

        environment_front = np.exp(
            -np.square((time_sec - env_arrival) / max(env_front_width, 1.0e-5))
        )
        environment_front *= env_strength * keep
        front_settle = 1.0 - float(
            smoothstep((time_sec - settle_start) / settle_duration)
        ) * settle_reduction
        wet_alpha = np.clip(
            environment_front * env_front_opacity * front_settle,
            0.0,
            0.40,
        )
        frame = frame * (1.0 - wet_alpha[..., None]) + wet_rgb * wet_alpha[..., None]

        for arrival, zone, region in region_fields:
            reveal_softness = max(float(region.get("reveal_softness", 0.24)), 1.0e-5)
            reveal = smoothstep((time_sec - arrival) / reveal_softness).astype(
                np.float32
            )
            region_start = float(region.get("start", region["blooms"][0]["start"]))
            causal_gate = float(
                smoothstep(
                    (time_sec - region_start + 0.12)
                    / max(float(region.get("gate_duration", 0.34)), 1.0e-5)
                )
            )
            local_alpha = reveal * zone * causal_gate
            frame = (
                frame * (1.0 - local_alpha[..., None])
                + master * local_alpha[..., None]
            )

            front_width = max(float(region.get("front_width", 0.105)), 1.0e-5)
            front = np.exp(-np.square((time_sec - arrival) / front_width))
            front *= zone * (0.30 + fibre_texture * 0.90) * causal_gate
            front_opacity = float(region.get("front_opacity", 0.30))
            front_alpha = np.clip(
                front * front_opacity * front_settle,
                0.0,
                0.45,
            )
            trace = np.asarray(
                region.get("trace_rgb", [42.0, 46.0, 45.0]),
                dtype=np.float32,
            )
            frame = (
                frame * (1.0 - front_alpha[..., None])
                + trace * front_alpha[..., None]
            )

            lock_config = region.get("lock", {})
            lock_start = float(lock_config.get("start", region_start + 1.8))
            lock_duration = max(float(lock_config.get("duration", 0.72)), 1.0e-5)
            lock = float(smoothstep((time_sec - lock_start) / lock_duration))
            lock_alpha = lock_masks[region["name"]] * lock
            frame = (
                frame * (1.0 - lock_alpha[..., None])
                + master * lock_alpha[..., None]
            )

        frame = camera_breath(
            frame,
            time_sec,
            duration,
            config.get("camera", {}),
        )
        process.stdin.write(
            np.uint8(np.clip(frame + 0.5, 0.0, 255.0)).tobytes()
        )

    process.stdin.close()
    return_code = process.wait()
    if return_code != 0:
        raise SystemExit(return_code)

    manifest = {
        "output": str(output),
        "duration": duration,
        "resolution": [width, height],
        "internal_fps": internal_fps,
        "output_fps": output_fps,
        "master": str(args.master.resolve()),
        "clean": str(args.clean.resolve()),
        "paper": str(args.paper.resolve()),
        "config": str(config_path),
        "environment_paths": len(config["environment_paths"]),
        "region_order": [region["name"] for region in config["regions"]],
        "negative_space_zones": len(config.get("negative_space", [])),
        "formation": (
            "shared environment arrival, regional fibrous blooms, exact late lock"
        ),
        "audio": "none",
    }
    output.with_name(f"render-manifest-{output.stem}.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(output)


if __name__ == "__main__":
    main()
