from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import cv2
import numpy as np


def smoothstep(edge0: float, edge1: float, value):
    scale = max(edge1 - edge0, 1.0e-6)
    x = np.clip((value - edge0) / scale, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def parse_pair(value: str) -> tuple[float, float]:
    parts = [float(part.strip()) for part in value.split(",")]
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("expected two comma-separated numbers")
    return parts[0], parts[1]


def normalize(field: np.ndarray, percentile: float = 98.5) -> np.ndarray:
    scale = float(np.percentile(np.abs(field), percentile))
    return np.clip(field / max(scale, 1.0e-6), -1.0, 1.0)


def make_fibre_field(height: int, width: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    noise = rng.normal(0.0, 1.0, (height, width)).astype(np.float32)
    horizontal = cv2.GaussianBlur(noise, (31, 3), 0)
    crossed = cv2.GaussianBlur(noise, (5, 19), 0)
    grain = cv2.GaussianBlur(noise, (3, 3), 0)
    field = 0.53 * horizontal + 0.29 * crossed + 0.18 * grain
    low, high = np.percentile(field, [1.5, 98.5])
    return np.clip((field - low) / max(high - low, 1.0e-6), 0.0, 1.0)


def wave_state(
    t: float,
    width: int,
    height: int,
    center_x: float,
    center_y: float,
    radius_x: float,
    radius_y: float,
    fibre: np.ndarray,
    period: float,
    wavelength: float,
    front_speed: float,
) -> tuple[np.ndarray, np.ndarray]:
    yy, xx = np.mgrid[0:height, 0:width].astype(np.float32)
    gx = (xx - center_x) / max(radius_x, 1.0)
    gy = (yy - center_y) / max(radius_y, 1.0)
    radius = np.sqrt(gx * gx + gy * gy)
    angle = np.arctan2(gy, gx)

    irregular_radius = radius + (
        0.014 * np.sin(angle * 5.0 + 0.10 * t)
        + 0.008 * np.sin(angle * 11.0 - 0.16 * t)
    )
    phase = 2.0 * np.pi * (
        irregular_radius / max(wavelength, 1.0e-4)
        - t / max(period, 1.0e-4)
    )
    front = min(1.16, 0.20 + front_speed * t)
    front_gate = 1.0 - smoothstep(front - 0.055, front + 0.075, radius)
    onset = smoothstep(0.0, 0.38, t)
    center_release = smoothstep(0.035, 0.115, radius)
    attenuation = np.exp(-0.86 * radius)
    angular_energy = np.clip(
        0.88
        + 0.10 * np.sin(angle * 3.0 + 0.22)
        + 0.06 * np.sin(angle * 9.0 - 0.45),
        0.64,
        1.08,
    )

    height_field = (
        np.sin(phase)
        * attenuation
        * angular_energy
        * front_gate
        * onset
        * center_release
    )
    contact_pool = np.exp(-0.5 * (radius / 0.12) ** 2)
    height_field += (
        0.42
        * np.sin(-2.0 * np.pi * t / max(period, 1.0e-4))
        * contact_pool
        * onset
    )

    crest = np.power(np.clip(np.cos(phase), 0.0, 1.0), 8.0)
    trough = 0.28 * np.power(np.clip(-np.cos(phase), 0.0, 1.0), 10.0)
    fibre_break = 0.54 + 0.62 * fibre
    sparse_gaps = np.clip(
        0.76
        + 0.19 * np.sin(angle * 7.0 + radius * 24.0)
        + 0.13 * np.sin(angle * 15.0 - radius * 17.0),
        0.20,
        1.0,
    )
    pigment = (crest + trough) * attenuation * front_gate * onset
    pigment *= fibre_break * sparse_gaps * center_release
    pigment += contact_pool * 0.18 * onset
    pigment = cv2.GaussianBlur(
        np.clip(pigment, 0.0, 1.0), (0, 0), 0.46
    )
    return height_field.astype(np.float32), pigment.astype(np.float32)


def build_masks(
    raw_mask: np.ndarray,
    contact_y: float,
    body_threshold: float,
    reflection_low: float,
    reflection_high: float,
) -> tuple[np.ndarray, np.ndarray]:
    height, _ = raw_mask.shape
    yy = np.arange(height, dtype=np.float32)[:, None]
    body = smoothstep(body_threshold, min(body_threshold + 0.10, 0.995), raw_mask)
    body *= 1.0 - smoothstep(contact_y - 3.0, contact_y + 8.0, yy)
    body = cv2.GaussianBlur(
        cv2.dilate(body, np.ones((3, 3), np.uint8)), (0, 0), 0.50
    )

    reflection = smoothstep(reflection_low, reflection_high, raw_mask)
    reflection *= 1.0 - smoothstep(
        body_threshold, min(body_threshold + 0.10, 0.995), raw_mask
    )
    reflection *= smoothstep(contact_y - 2.0, contact_y + 18.0, yy)
    reflection = cv2.GaussianBlur(reflection, (0, 0), 1.2)
    return body.astype(np.float32), reflection.astype(np.float32)


def refract_reflection(
    plate: np.ndarray,
    reflection_mask: np.ndarray,
    height_field: np.ndarray,
    contact_x: float,
    contact_y: float,
    radius_x: float,
    displacement_x: float,
    displacement_y: float,
) -> np.ndarray:
    height, width = reflection_mask.shape
    yy, xx = np.mgrid[0:height, 0:width].astype(np.float32)
    grad_x = normalize(cv2.Sobel(height_field, cv2.CV_32F, 1, 0, ksize=3))
    grad_y = normalize(cv2.Sobel(height_field, cv2.CV_32F, 0, 1, ksize=3))

    depth = np.maximum(yy - contact_y, 0.0)
    half_width = np.clip(radius_x * 0.82 - depth * 0.34, radius_x * 0.49, radius_x * 0.82)
    horizontal_distance = np.abs(xx - contact_x) / np.maximum(half_width, 1.0)
    manual_roi = 1.0 - smoothstep(0.82, 1.02, horizontal_distance)
    manual_roi *= smoothstep(contact_y + 1.0, contact_y + 18.0, yy)
    manual_roi *= np.exp(-depth / max(height * 0.32, 1.0))
    expanded = cv2.GaussianBlur(
        cv2.dilate(reflection_mask, np.ones((11, 11), np.uint8)),
        (0, 0),
        2.4,
    )
    region = np.clip(np.maximum(expanded, manual_roi * 0.92), 0.0, 1.0)
    anchor = smoothstep(contact_y + 1.0, contact_y + 22.0, yy)
    spatial = region * anchor

    map_x = np.clip(
        xx + (grad_x * displacement_x + height_field * 1.2) * spatial,
        0.0,
        width - 1.001,
    )
    map_y = np.clip(
        yy + (grad_y * displacement_y + height_field * 3.4) * spatial,
        0.0,
        height - 1.001,
    )
    warped = cv2.remap(
        plate,
        map_x,
        map_y,
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT_101,
    )
    blend = np.clip(spatial, 0.0, 0.98)[..., None]
    result = plate.astype(np.float32) * (1.0 - blend)
    result += warped.astype(np.float32) * blend
    result += (
        cv2.GaussianBlur(height_field, (0, 0), 0.8)
        * spatial
        * 5.2
    )[..., None]
    return np.clip(result, 0.0, 255.0).astype(np.uint8)


def composite_ink(
    background: np.ndarray,
    pigment: np.ndarray,
    deposit: np.ndarray,
    fibre: np.ndarray,
    protected_plate: np.ndarray,
    body_mask: np.ndarray,
) -> np.ndarray:
    moving = np.power(np.clip(pigment, 0.0, 1.0), 0.76)
    settled = np.power(np.clip(deposit, 0.0, 1.0), 1.20)
    grad_x = cv2.Sobel(moving, cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(moving, cv2.CV_32F, 0, 1, ksize=3)
    wet_edge = np.clip(
        np.sqrt(grad_x * grad_x + grad_y * grad_y)
        / max(
            float(
                np.percentile(
                    np.sqrt(grad_x * grad_x + grad_y * grad_y), 98.5
                )
            ),
            1.0e-6,
        ),
        0.0,
        1.0,
    )
    granulation = 0.72 + 0.42 * fibre
    broken = smoothstep(0.16, 0.84, fibre)
    alpha = (
        0.56 * moving * granulation
        + 0.12 * settled * (0.74 + 0.30 * broken)
        + 0.28 * wet_edge * moving
    )
    alpha = cv2.GaussianBlur(
        np.clip(alpha, 0.0, 0.93), (0, 0), 0.42
    )
    ink_colour = np.full_like(background, (21.0, 22.0, 20.0), dtype=np.float32)
    result = background.astype(np.float32) * (1.0 - alpha[..., None])
    result += ink_colour * alpha[..., None]
    mask = np.clip(body_mask[..., None], 0.0, 1.0)
    result = result * (1.0 - mask) + protected_plate.astype(np.float32) * mask
    return np.clip(result, 0.0, 255.0).astype(np.uint8)


def open_encoder(path: Path, width: int, height: int, fps: int):
    path.parent.mkdir(parents=True, exist_ok=True)
    return subprocess.Popen(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "bgr24",
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
            "slow",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(path),
        ],
        stdin=subprocess.PIPE,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Render anisotropic ink ripples and refract a product reflection "
            "from one shared shallow-water height field."
        )
    )
    parser.add_argument("--plate", type=Path, required=True)
    parser.add_argument("--product-mask", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--duration", type=float, default=4.5)
    parser.add_argument("--width", type=int, default=0)
    parser.add_argument("--height", type=int, default=0)
    parser.add_argument("--internal-fps", type=int, default=48)
    parser.add_argument("--output-fps", type=int, default=24)
    parser.add_argument("--contact", type=parse_pair, default=(0.5, 0.8385))
    parser.add_argument("--radius", type=parse_pair, default=(0.3333, 0.0411))
    parser.add_argument("--period", type=float, default=1.72)
    parser.add_argument("--wavelength", type=float, default=0.225)
    parser.add_argument("--front-speed", type=float, default=0.245)
    parser.add_argument("--reflection-displacement", type=parse_pair, default=(5.4, 11.6))
    parser.add_argument("--body-threshold", type=float, default=0.86)
    parser.add_argument("--reflection-thresholds", type=parse_pair, default=(0.30, 0.73))
    parser.add_argument("--seed", type=int, default=20260730)
    args = parser.parse_args()

    if args.internal_fps != args.output_fps * 2:
        raise ValueError("internal fps must be exactly twice output fps")
    plate_source = cv2.imread(str(args.plate), cv2.IMREAD_COLOR)
    mask_source = cv2.imread(str(args.product_mask), cv2.IMREAD_GRAYSCALE)
    if plate_source is None or mask_source is None:
        raise RuntimeError("could not read plate or product mask")

    source_height, source_width = plate_source.shape[:2]
    width = args.width or source_width
    height = args.height or source_height
    size = (width, height)
    plate = cv2.resize(
        plate_source, size, interpolation=cv2.INTER_LANCZOS4
    )
    raw_mask = (
        cv2.resize(mask_source, size, interpolation=cv2.INTER_AREA).astype(
            np.float32
        )
        / 255.0
    )

    contact_x = args.contact[0] * width
    contact_y = args.contact[1] * height
    radius_x = args.radius[0] * width
    radius_y = args.radius[1] * height
    body_mask, reflection_mask = build_masks(
        raw_mask,
        contact_y,
        args.body_threshold,
        args.reflection_thresholds[0],
        args.reflection_thresholds[1],
    )
    fibre = make_fibre_field(height, width, args.seed)
    deposit = np.zeros((height, width), np.float32)
    internal_frames: list[np.ndarray] = []

    for frame_index in range(int(round(args.duration * args.internal_fps))):
        t = frame_index / args.internal_fps
        height_field, pigment = wave_state(
            t,
            width,
            height,
            contact_x,
            contact_y,
            radius_x,
            radius_y,
            fibre,
            args.period,
            args.wavelength,
            args.front_speed,
        )
        deposit = np.maximum(deposit * 0.9988, pigment * 0.105)
        water_plate = refract_reflection(
            plate,
            reflection_mask,
            height_field,
            contact_x,
            contact_y,
            radius_x,
            args.reflection_displacement[0],
            args.reflection_displacement[1],
        )
        internal_frames.append(
            composite_ink(
                water_plate,
                pigment,
                deposit,
                fibre,
                plate,
                body_mask,
            )
        )

    encoder = open_encoder(args.output, width, height, args.output_fps)
    assert encoder.stdin is not None
    for index in range(0, len(internal_frames) - 1, 2):
        blended = cv2.addWeighted(
            internal_frames[index],
            0.5,
            internal_frames[index + 1],
            0.5,
            0.0,
        )
        encoder.stdin.write(blended.tobytes())
    encoder.stdin.close()
    if encoder.wait() != 0:
        raise RuntimeError("ffmpeg encoder failed")

    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(
            json.dumps(
                {
                    "effect": "shared-shallow-water-ink-reflection",
                    "duration_seconds": args.duration,
                    "resolution": [width, height],
                    "internal_fps": args.internal_fps,
                    "output_fps": args.output_fps,
                    "contact": [contact_x, contact_y],
                    "radius": [radius_x, radius_y],
                    "wave": {
                        "period_seconds": args.period,
                        "wavelength_normalized": args.wavelength,
                        "front_speed_normalized_per_second": args.front_speed,
                    },
                    "reflection_displacement": list(
                        args.reflection_displacement
                    ),
                    "causality": (
                        "one height field drives pigment crests, wet-edge "
                        "lighting and reflection refraction"
                    ),
                    "product_body_locked": True,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
