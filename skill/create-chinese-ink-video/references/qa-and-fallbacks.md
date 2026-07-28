# QA and fallbacks

## Static style board

Approve only when:

- all test subjects belong to one visual system
- invariants are visible without reading the prompt
- people and engineered objects remain structurally legible
- accent colors retain their assigned role
- negative space and density match the selected direction
- there is no fake text, fake logo, watermark or unexplained symbol

## Dynamic style proof

Play at normal speed and check:

- the primary style event is understandable
- formation is material-specific, not a generic mask or fade
- camera, subject and effect do not compete
- the subject remains stable through the effect
- the completion frame is usable as a composition
- the final state settles or hands off intentionally
- proof frames match the actual video

## Full-video continuity

Compare representative frames from every shot:

- paper/base and black/neutral range
- accent color frequency and role
- subject treatment and realism level
- mark-making scale and density
- camera intensity and transition family
- character, product and architecture locks
- primary-entity exposure count and narrative role
- text, brand and document policy compliance

Review two separate artifacts:

- one representative frame per shot for repetition and continuity
- transition strips around every cut for cadence and material handoff

Play the full preview at normal speed. Use frame-delta statistics to locate suspicious timestamps,
not to replace visual judgment. Compare a revision against its own baseline because legitimate cuts
and high-motion shots naturally produce different values.

## Failure routing

| Failure | Required response |
|---|---|
| Style works only on the reference subject | Return to Gate 2 and test a different subject class |
| Images look related but not identical in language | Tighten 3–5 invariants; reduce optional adjectives |
| Static frame works but motion feels generic | Return to Gate 3 and define a material-specific formation event |
| Ink looks like a smooth mask | Add fibre-driven edge breakup, pooling and granulation; remove radial reveal |
| Subject melts or changes geometry | Separate atmosphere wash from structural contour; lock or composite the subject |
| Motion is overloaded | Keep one dominant channel and reduce camera or effect strength |
| Generative shot drifts | Shorten, reduce camera movement, strengthen reference, or use hybrid compositing |
| Accent color spreads across the frame | Restore focal-role constraint and regenerate only affected shots |
| Fake text or logo appears | Remove it from generation and composite supplied artwork deterministically |
| Hero entity repeats without a new role | Remove, replace or justify the later shot before full render |
| Deleting a shot changes runtime unexpectedly | Apply the recorded compact, redistribute or replace policy |
| Transition feels stuck or flashes | Inspect transition strip and frame-delta peaks; lengthen or redesign the material handoff |
| Native render fails but snapshots work | Use resumable batched snapshots and FFmpeg encoding; verify the full expected sequence |
| Final render differs from preview | Stop delivery, reproduce the approved state and rerun QA |

## Versioning

Use `v01`, `v02`, and so on for boards and previews. Increment `style-bible.json` semantically when invariants or public behavior change. Never overwrite an artifact already shown to the user.
