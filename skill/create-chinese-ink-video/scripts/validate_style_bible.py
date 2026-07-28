#!/usr/bin/env python3
"""Validate the stable contract of a video style-bible JSON file."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REQUIRED = [
    "name",
    "version",
    "visual_thesis",
    "invariants",
    "variation_axes",
    "palette",
    "materials",
    "composition",
    "subject_treatment",
    "camera_language",
    "motion_grammar",
    "negative_constraints",
    "generator_adapters",
    "fallbacks",
]


def validate(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["Root must be a JSON object."]

    for key in REQUIRED:
        if key not in data:
            errors.append(f"Missing required field: {key}")

    name = data.get("name")
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        errors.append("name must be lowercase hyphen-case.")

    version = data.get("version")
    if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", version):
        errors.append("version must use semantic form such as 1.0.0.")

    thesis = data.get("visual_thesis")
    if not isinstance(thesis, str) or len(thesis.strip()) < 20:
        errors.append("visual_thesis must be an observable sentence of at least 20 characters.")

    invariants = data.get("invariants")
    if not isinstance(invariants, list) or not 3 <= len(invariants) <= 7:
        errors.append("invariants must contain 3–7 items.")
    elif any(not isinstance(item, str) or len(item.strip()) < 8 for item in invariants):
        errors.append("each invariant must be a descriptive string of at least 8 characters.")

    for key in ("variation_axes", "composition", "subject_treatment", "camera_language"):
        value = data.get(key)
        if not isinstance(value, dict) or not value:
            errors.append(f"{key} must be a non-empty object.")

    palette = data.get("palette")
    if not isinstance(palette, dict):
        errors.append("palette must be an object.")
    else:
        for key in ("paper", "neutral", "accent", "forbidden"):
            if key not in palette or not isinstance(palette[key], list):
                errors.append(f"palette.{key} must be an array.")

    motion = data.get("motion_grammar")
    if not isinstance(motion, dict):
        errors.append("motion_grammar must be an object.")
    else:
        for key in ("formation", "subject", "transition", "settle"):
            if key not in motion:
                errors.append(f"motion_grammar.{key} is required.")

    for key in ("materials", "negative_constraints", "fallbacks"):
        value = data.get(key)
        if not isinstance(value, list) or not value:
            errors.append(f"{key} must be a non-empty array.")

    if not isinstance(data.get("generator_adapters"), dict):
        errors.append("generator_adapters must be an object.")

    return errors


def self_test() -> int:
    valid = {
        "name": "test-style",
        "version": "1.0.0",
        "visual_thesis": "A visible and testable visual world with stable material behavior.",
        "invariants": ["Visible paper base", "One dominant gesture", "Stable subject structure"],
        "variation_axes": {"intensity": {"default": 0.5}},
        "palette": {"paper": ["ivory"], "neutral": ["black"], "accent": [], "forbidden": []},
        "materials": ["paper"],
        "composition": {"focus": "one"},
        "subject_treatment": {"objects": "stable"},
        "camera_language": {"movement": "restrained"},
        "motion_grammar": {"formation": [], "subject": [], "transition": [], "settle": "hold"},
        "negative_constraints": ["generic fade"],
        "generator_adapters": {},
        "fallbacks": ["simplify movement"],
    }
    if validate(valid):
        print("Self-test failed: valid fixture was rejected.", file=sys.stderr)
        return 1
    invalid = dict(valid)
    invalid["name"] = "Bad_Name"
    if not validate(invalid):
        print("Self-test failed: invalid fixture was accepted.", file=sys.stderr)
        return 1
    print("Self-test passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("style_bible", nargs="?", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if args.style_bible is None:
        parser.error("style_bible is required unless --self-test is used")

    try:
        data = json.loads(args.style_bible.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    errors = validate(data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"OK: {args.style_bible}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
