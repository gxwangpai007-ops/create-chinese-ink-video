#!/usr/bin/env python3
"""Build a reusable hybrid Chinese-ink layer pack from an approved master and masks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


LAYER_NAMES = (
    "00-paper-base.png",
    "01-ambient-clean-environment.png",
    "02-approved-background-structure.png",
    "03-primary-object.png",
    "04-subject-body.png",
    "05-hands-tool-detail.png",
    "06-accent.png",
)


def read_rgb(path: Path, size: tuple[int, int] | None = None) -> Image.Image:
    image = Image.open(path).convert("RGB")
    if size and image.size != size:
        raise ValueError(f"{path} is {image.size}; expected {size}")
    return image


def read_mask(path: Path | None, size: tuple[int, int]) -> np.ndarray:
    if path is None:
        return np.zeros((size[1], size[0]), dtype=np.uint8)
    image = Image.open(path)
    if image.size != size:
        raise ValueError(f"{path} is {image.size}; expected {size}")
    if "A" in image.getbands():
        image = image.getchannel("A")
    else:
        image = image.convert("L")
    return np.where(np.asarray(image) >= 128, 255, 0).astype(np.uint8)


def rgba(rgb: np.ndarray, mask: np.ndarray, feather: float) -> Image.Image:
    alpha = Image.fromarray(mask)
    if feather > 0:
        alpha = alpha.filter(ImageFilter.GaussianBlur(feather))
    image = Image.fromarray(rgb).convert("RGBA")
    image.putalpha(alpha)
    return image


def auto_accent(rgb: np.ndarray) -> np.ndarray:
    red = rgb[:, :, 0].astype(np.int16)
    green = rgb[:, :, 1].astype(np.int16)
    blue = rgb[:, :, 2].astype(np.int16)
    return np.where(
        (red > 92)
        & (red > green * 1.22)
        & (green > blue * 0.82)
        & ((red - blue) > 32),
        255,
        0,
    ).astype(np.uint8)


def save_contact_sheet(layers: list[tuple[str, Image.Image]], path: Path) -> None:
    cell_w, cell_h, label_h, columns = 282, 502, 34, 3
    rows = (len(layers) + columns - 1) // columns
    sheet = Image.new("RGB", (cell_w * columns, (cell_h + label_h) * rows), "#1c1c1a")
    draw = ImageDraw.Draw(sheet)
    for index, (name, image) in enumerate(layers):
        backing = Image.new("RGBA", image.size, (237, 232, 220, 255))
        backing.alpha_composite(image)
        backing.thumbnail((cell_w, cell_h), Image.Resampling.LANCZOS)
        x0 = (index % columns) * cell_w
        y0 = (index // columns) * (cell_h + label_h)
        x = x0 + (cell_w - backing.width) // 2
        y = y0 + (cell_h - backing.height) // 2
        sheet.paste(backing.convert("RGB"), (x, y))
        draw.text((x0 + 8, y0 + cell_h + 8), name, fill="#eeeeea")
    sheet.save(path, quality=92)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", required=True, type=Path)
    parser.add_argument("--paper", required=True, type=Path)
    parser.add_argument("--clean-plate", required=True, type=Path)
    parser.add_argument("--subject-mask", required=True, type=Path)
    parser.add_argument("--object-mask", required=True, type=Path)
    parser.add_argument("--detail-mask", type=Path)
    parser.add_argument("--accent-mask", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--ambient-strength", type=float, default=0.34)
    parser.add_argument("--background-threshold", type=int, default=242)
    parser.add_argument("--feather", type=float, default=0.8)
    args = parser.parse_args()

    if not 0 <= args.ambient_strength <= 1:
        parser.error("--ambient-strength must be between 0 and 1")
    if not 0 <= args.background_threshold <= 255:
        parser.error("--background-threshold must be between 0 and 255")
    if args.feather < 0:
        parser.error("--feather must be non-negative")

    master_image = read_rgb(args.master)
    size = master_image.size
    paper_image = read_rgb(args.paper, size)
    clean_image = read_rgb(args.clean_plate, size)
    rgb = np.asarray(master_image)
    gray = np.asarray(master_image.convert("L"))

    subject = read_mask(args.subject_mask, size)
    primary_object = read_mask(args.object_mask, size)
    detail = read_mask(args.detail_mask, size)
    accent = (
        read_mask(args.accent_mask, size)
        if args.accent_mask
        else auto_accent(rgb)
    )

    detail = np.where((detail > 0) & (subject > 0), 255, 0).astype(np.uint8)
    body = subject.copy()
    body[detail > 0] = 0
    primary_object[subject > 0] = 0
    occupied = np.maximum(subject, primary_object)
    background = np.where(occupied > 0, 0, 255).astype(np.uint8)
    structure = np.where(
        (background > 0) & (gray < args.background_threshold), 255, 0
    ).astype(np.uint8)

    for mask in (structure, primary_object, body, detail):
        mask[accent > 0] = 0

    ambient = Image.blend(
        paper_image, clean_image, args.ambient_strength
    ).convert("RGBA")
    layers = [
        (LAYER_NAMES[0], paper_image.convert("RGBA")),
        (LAYER_NAMES[1], ambient),
        (LAYER_NAMES[2], rgba(rgb, structure, args.feather + 0.4)),
        (LAYER_NAMES[3], rgba(rgb, primary_object, args.feather)),
        (LAYER_NAMES[4], rgba(rgb, body, args.feather)),
        (LAYER_NAMES[5], rgba(rgb, detail, max(0.25, args.feather * 0.6))),
        (LAYER_NAMES[6], rgba(rgb, accent, max(0.2, args.feather * 0.45))),
    ]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, image in layers:
        image.save(args.output_dir / name)

    composite = layers[0][1].copy()
    for _, layer in layers[1:]:
        composite.alpha_composite(layer)
    composite.save(args.output_dir / "composite.png")
    save_contact_sheet(layers, args.output_dir / "contact-sheet.jpg")

    manifest = {
        "master": str(args.master.resolve()),
        "paper": str(args.paper.resolve()),
        "clean_plate": str(args.clean_plate.resolve()),
        "size": list(size),
        "ambient_strength": args.ambient_strength,
        "background_threshold": args.background_threshold,
        "layers": [name for name, _ in layers],
        "policies": {
            "style_reference": "material-only",
            "foreground": "approved-master exact pixels",
            "occluded_background": "clean environment backing",
        },
    }
    (args.output_dir / "layer-pack.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"OK: {args.output_dir}")
    print(f"layers={len(layers)} size={size[0]}x{size[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
