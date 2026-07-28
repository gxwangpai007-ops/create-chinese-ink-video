# Assembly and revision

## 1. Shot manifest contract

Store shots as a top-level `shots` array or as the JSON root array. Give every shot:

```json
{
  "shot_id": "S04",
  "start": 11.2,
  "end": 15.7,
  "primary_entity": "delivery_van",
  "narrative_role": "employment",
  "appearance_index": 2,
  "repeat_allowed": false,
  "repeat_reason": null,
  "transition_in": "paper-reset",
  "transition_out": "ink-seed",
  "deletion_duration_policy": "compact"
}
```

Use a stable entity ID for the same character, vehicle, product, building or document across
shots. Do not use changing prose descriptions as IDs.

Allow a repeated hero entity only when the repeat has a distinct role, reveals new information,
creates a deliberate motif, or establishes continuity. Record that reason. A different crop or
camera angle alone is not a reason.

## 2. Assembly audit

Before full animation:

1. Build a sheet containing one representative frame from every shot in timeline order.
2. Read the sheet as an edit, not as isolated illustrations.
3. Mark repeated entities, repeated narrative roles, adjacent similar compositions and dead shots.
4. Confirm every shot changes information, emotion, location, time or state.
5. Confirm each transition has one visual handoff.
6. Run `audit_shot_manifest.py`; resolve every error.

For `text_policy: none`, reject added titles, captions, labels, disclaimers and generated pseudo-text.
Pure graphic symbols are allowed only when the brief permits `graphics_only`. Embedded text already
inside an approved source asset follows `brand_policy`, not the caption policy.

## 3. Transition grammar

Prefer one of these handoffs:

- `ink-carry`: an existing stroke continues into the next composition
- `paper-reset`: the old image retreats into fibre and leaves controlled paper space
- `ink-seed`: a dot, dry-brush edge or pooled wash begins the next image
- `shape-match`: a structural contour becomes the next subject

Do not use a generic opacity crossfade as the only explanation for a water-ink transition. It may
support a material event, but the viewer should perceive fibre breakup, pooling, dry-brush locking
or an intentional paper reset.

Build transition strips around every cut. Sample before, during and after the handoff; inspect at
normal speed as well as frame by frame.

## 4. Revision duration policy

When removing a shot, apply the brief's policy:

- `compact`: remove the duration and shorten the video
- `redistribute`: extend neighboring shots without changing the total duration
- `replace`: create a new shot with a different entity or narrative role

If no policy exists, use `compact` for a rough preview and state the new duration. Do not silently
stretch still frames to preserve runtime.

Keep the approved version. Write the revision to a new version and record:

- source version
- changed shots and ranges
- new duration
- approval invalidated by the change
- checks rerun

## 5. Local rerender and deterministic fallback

For a localized HyperFrames change:

1. Expand each affected range to include the complete transition plus two output frames of handles.
2. Run `snapshot_frame_ranges.py --dry-run`.
3. Capture at an internal rate of 48 fps when the output is 24 fps.
4. Replace only the mapped global frames in a copied sequence.
5. Encode the copied sequence to a new MP4.
6. Run full decode, metadata, frame-delta and transition-strip checks.

When native video rendering fails but deterministic snapshots work, use:

```text
HyperFrames check
→ batched snapshots
→ resumable global frame sequence
→ optional two-frame temporal blend
→ CFR H.264 encoding
→ full decode scan
→ frame-delta report
→ shot sheet and transition strips
```

Do not claim success from a partial sequence. Verify expected frame count equals
`duration × internal_fps`.
