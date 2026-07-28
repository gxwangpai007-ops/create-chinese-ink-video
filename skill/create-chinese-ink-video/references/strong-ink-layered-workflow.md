# Strong Ink Layered Workflow

Use this profile when a user wants the forceful B-style texture proven by dense carbon ink, dry-brush flying white, splatter and sparse orange-red accents, while keeping a supplied person, product or engineered object structurally stable.

## 1. Separate reference responsibilities

For style transfer with two references:

- **Target reference** owns content, identity, pose, crop, camera, subject geometry and scene.
- **Style reference** owns only paper, ink density, brush character, edge breakup, granulation and accent behavior.

State both roles explicitly. List content that must not migrate from the style reference. For example, a vehicle style reference must not introduce the vehicle, road, rain, logo or city composition into a factory-worker target.

Generate two calibrated candidates when strength is unresolved:

| Candidate | Ink abstraction | Use |
|---|---:|---|
| B1 | about 70% | more literal structure and environment detail |
| B2 | about 85% | stronger carbon masses, flying white and expressive impact |

Prefer B2 when the user asks for the texture of the forceful vehicle reference. Do not make the face unreadable: reduce skin to 2–3 controlled wash planes plus contour while preserving identity, glasses, gaze and anatomy.

## 2. Lock the approved completion frame

After approval:

- Preserve the approved master as a versioned immutable artifact.
- Extract subject, hands/tools and engineered objects from the approved master; do not regenerate them for the Layer Pack.
- Allow a clean environment plate to differ only in occluded regions.
- Compare the finished composite against the approved master before animation.

## 3. Use the hybrid seven-layer pack

Default order:

1. `00-paper-base`
2. `01-ambient-clean-environment`
3. `02-approved-background-structure`
4. `03-primary-object`
5. `04-subject-body`
6. `05-hands-tool-detail`
7. `06-accent`

Not every shot needs seven layers. Keep this order when a human interacts with an engineered object and hands/tools need a separate structural lock.

### Anti-hole rule

Never place foreground cutouts directly over bare paper when their absence exposes a large human- or object-shaped hole. Put a compatible worker-free or object-free environment plate underneath first.

Preferred backing:

```text
paper
→ pale clean environment blended toward paper at about 0.25–0.40
→ approved background ink structure outside foreground occlusion
→ exact foreground layers
```

Do not use large automatic inpainting as the default for a human-sized occlusion. It often creates stretched polygons, radial smears or obvious synthetic fill. Prefer, in order:

1. an approved or generated clean environment plate;
2. an existing compatible empty plate softened toward paper;
3. a deliberately pale atmospheric wash with reduced detail.

If none exists, stop at the Layer Pack gate or simplify the formation. Do not accept a silhouette-shaped white hole.

Run the deterministic pack builder when masks are available:

```bash
python <skill-dir>/scripts/build_hybrid_layer_pack.py \
  --master <approved-master.png> \
  --paper <paper.png> \
  --clean-plate <empty-environment.png> \
  --subject-mask <subject-mask.png> \
  --object-mask <object-mask.png> \
  --detail-mask <hands-tool-mask.png> \
  --output-dir <project>/assets/layers-vNN
```

## 4. Formation order

Use one dominant formation event:

```text
paper fibre
→ pale environment wash
→ structural background ink
→ engineered-object perspective path
→ clothing/body ink pools
→ face, hands and tool contour lock
→ sparse accent
→ settle
```

- Use wet wash for atmosphere and dry brush for stable geometry.
- Reassign sorted reveal marks to evenly spaced arrival values when random clustering creates a visible jump.
- Let terminal coverage converge continuously; never hard-fill a whole layer on the final reveal frame.
- Do not animate a foreground cutout strongly enough to expose missing pixels behind it.

## 5. Smooth-preview standard

For a 24 fps delivery proof:

1. Capture a complete deterministic sequence at 48 fps.
2. Verify frame count equals `duration × 48`.
3. Apply a two-frame temporal mix.
4. Encode CFR H.264 at 24 fps.
5. Run full decode, metadata probe and frame-delta analysis.

Use:

```bash
python <skill-dir>/scripts/encode_smooth_preview.py \
  <frames-48-dir> -o <preview.mp4> \
  --internal-fps 48 --output-fps 24
```

Frame-delta peaks locate suspect moments; they do not approve aesthetics. Inspect peak neighborhoods at normal speed and compare against the previous accepted version.

## 6. Approval gates

Keep these approvals separate:

1. B1/B2 static style strength.
2. Layer Pack composite and anti-hole check.
3. Normal-speed 3–5 second motion proof.
4. Full-video expansion.

Approval of B2 does not automatically approve unseen layer extraction or motion.
