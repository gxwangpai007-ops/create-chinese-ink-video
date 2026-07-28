#!/usr/bin/env python3
"""Audit shot-manifest entity exposure, narrative roles, and repeat justification."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def load_shots(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    shots = data.get("shots") if isinstance(data, dict) else data
    if not isinstance(shots, list) or not all(isinstance(item, dict) for item in shots):
        raise ValueError("manifest must be a JSON array or an object containing a shots array")
    return shots


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()

    shots = load_shots(args.manifest)
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    entity_occurrences: dict[str, list[dict[str, Any]]] = defaultdict(list)
    role_occurrences: dict[str, list[str]] = defaultdict(list)

    for position, shot in enumerate(shots, start=1):
        shot_id = str(shot.get("shot_id") or shot.get("id") or f"shot-{position:02d}")
        entities = as_list(shot.get("primary_entity", shot.get("primary_entities")))
        if not entities:
            warnings.append({"shot_id": shot_id, "code": "missing_primary_entity"})
            asset = str(shot.get("asset") or "").strip()
            if asset:
                entities = [f"asset:{asset}"]
        explicit_role = str(shot.get("narrative_role") or "").strip()
        role = explicit_role or str(shot.get("narrative_function") or "").strip()

        if not explicit_role:
            warnings.append({"shot_id": shot_id, "code": "missing_narrative_role"})
        if role:
            role_occurrences[role].append(shot_id)

        for entity in entities:
            entity_occurrences[entity].append(
                {
                    "shot_id": shot_id,
                    "appearance_index": shot.get("appearance_index"),
                    "repeat_allowed": bool(shot.get("repeat_allowed", False)),
                    "repeat_reason": str(shot.get("repeat_reason") or "").strip(),
                    "narrative_role": role,
                }
            )

    for entity, occurrences in sorted(entity_occurrences.items()):
        for expected_index, occurrence in enumerate(occurrences, start=1):
            actual_index = occurrence["appearance_index"]
            if actual_index is None:
                warnings.append(
                    {
                        "shot_id": occurrence["shot_id"],
                        "entity": entity,
                        "code": "missing_appearance_index",
                        "expected": expected_index,
                    }
                )
            elif actual_index != expected_index:
                warnings.append(
                    {
                        "shot_id": occurrence["shot_id"],
                        "entity": entity,
                        "code": "appearance_index_mismatch",
                        "expected": expected_index,
                        "actual": actual_index,
                    }
                )

            if expected_index > 1 and (
                not occurrence["repeat_allowed"] or not occurrence["repeat_reason"]
            ):
                errors.append(
                    {
                        "shot_id": occurrence["shot_id"],
                        "entity": entity,
                        "code": "unjustified_entity_repeat",
                        "message": "later appearances require repeat_allowed=true and repeat_reason",
                    }
                )

    for role, shot_ids in sorted(role_occurrences.items()):
        if len(shot_ids) > 1:
            warnings.append(
                {
                    "code": "repeated_narrative_role",
                    "narrative_role": role,
                    "shot_ids": shot_ids,
                }
            )

    report = {
        "manifest": str(args.manifest),
        "shot_count": len(shots),
        "entity_count": len(entity_occurrences),
        "errors": errors,
        "warnings": warnings,
        "ok": not errors,
    }
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
