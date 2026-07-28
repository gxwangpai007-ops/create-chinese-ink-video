# Prompt construction

Build prompts from the approved Style Bible instead of copying one master prompt into every shot.

## Prompt order

1. State the shot's narrative purpose and subject.
2. Describe composition, scale and camera position.
3. Apply the style thesis.
4. Add only the relevant invariants.
5. Specify materials and mark-making.
6. State lighting, atmosphere and color roles.
7. State the completion frame, not only the effect.
8. Add shot-specific negative constraints.

## Component template

```text
Create a {shot_type} for {narrative_purpose}.

Subject:
{subject and required structure}

Composition and camera:
{foreground/midground/background, framing, perspective, lens behavior}

Style system:
{visual_thesis}
Maintain: {relevant invariants}

Materials and formation:
{surface, mark-making, formation sequence, completion state}

Color and light:
{paper/base, neutral range, accent role, atmosphere}

Continuity:
{character/product/architecture locks and previous-shot carryover}

Avoid:
{global negatives plus shot-specific failures}
```

## Adapter rule

Keep the semantic components stable and translate only syntax, length and supported controls for a target generator. Record seed, reference image, model version, aspect ratio and strength when the tool exposes them.

Do not use artist names as a substitute for observable style rules. Do not request text or logos from a raster generator when deterministic compositing is available.
