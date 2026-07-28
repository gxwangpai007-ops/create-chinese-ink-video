# Renderer routing

Choose the route after the Style Bible and proof-shot blueprint exist.

## Deterministic route

Use HyperFrames with DOM/SVG/Canvas/WebGL, GSAP or equivalent deterministic timelines, then render through FFmpeg.

Prefer for:

- precise typography and logos
- paper texture and controlled ink mattes
- repeatable transitions and timing
- layered parallax
- exact aspect-ratio variants
- fixes that must not regenerate the whole shot

For local revisions, prefer deterministic frame-range rerender over rebuilding unaffected shots.
Capture enough handles to cover the whole transition, render into a copied global sequence and
deliver a new version.

## Generative route

Use an available image-to-video or text-to-video model when natural subject motion, complex camera travel or fluid environment behavior dominates.

Before generation:

- lock the approved keyframe or reference
- specify start, action and completion state
- state camera behavior separately
- include Style Bible invariants and negatives
- record model, version, seed/reference and parameters when available

Generate a low-cost preview first. Do not repeatedly retry the same quota, permission or unsupported-control error.

## Hybrid route

Default to hybrid for expressive ink:

- Let generation handle people, vehicles, weather and complex physical motion.
- Let deterministic composition handle paper, ink formation, typography, logos, color accents, shot transitions and final continuity.

Avoid stacking two independent random ink simulations. Decide which layer owns the material behavior.

## Failure route

Use:

```text
generative drift
→ shorten the shot or reduce camera motion
→ lock a stronger keyframe/reference
→ move ink formation and typography to deterministic compositing
→ regenerate only the natural-motion plate
```

If no video generator is available, continue with a deterministic proof rather than blocking the entire style workflow.

If HyperFrames video rendering fails while `check` and `snapshot` work, use the deterministic
snapshot fallback in `assembly-and-revision.md`. Treat a complete verified frame sequence as the
source of truth; do not mix frames from different composition revisions.
