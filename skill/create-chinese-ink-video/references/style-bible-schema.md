# Style Bible contract

Use this contract after the static style board is approved. Keep the Style Bible independent of any particular generator. Store tool-specific wording under `generator_adapters`.

## Required fields

| Field | Purpose |
|---|---|
| `name` | Stable lowercase hyphenated style ID |
| `version` | Incremented Style Bible version |
| `visual_thesis` | One observable sentence describing the visual world |
| `invariants` | Features that must survive every shot |
| `variation_axes` | Named dimensions that may change within bounded ranges |
| `palette` | Base, ink/neutral, accent and forbidden colors |
| `materials` | Surface, mark-making and texture behavior |
| `composition` | Space, depth, density and focal rules |
| `subject_treatment` | Rules for people, objects, architecture and environments |
| `camera_language` | Lens, framing and camera behavior |
| `motion_grammar` | Formation, subject motion, transitions and settling |
| `negative_constraints` | Observable failure states and forbidden aesthetics |
| `generator_adapters` | Optional prompt or implementation deltas per tool |
| `fallbacks` | Pre-approved simplifications that retain the style |

## Authoring rules

- Write invariants as observable tests, not adjectives.
- Keep 3–7 invariants. If everything is invariant, the style cannot support storytelling.
- Give each variation axis a default, minimum and maximum or a finite set of allowed values.
- State color roles; do not list swatches without usage.
- Separate formation motion from camera and subject motion.
- Specify a completion state. A style effect must settle instead of drifting forever unless perpetual motion is intentional.
- Put tool-specific syntax in adapters, never in the visual thesis.
- Validate the file against `assets/style-bible.schema.json`.

## Minimal example

```json
{
  "name": "expressive-urban-ink",
  "version": "1.0.0",
  "visual_thesis": "A contemporary city is built from restrained rice-paper space, wet ink deposits and decisive calligraphic strokes while realistic subjects remain structurally legible.",
  "invariants": [
    "Warm off-white paper remains visible in every shot.",
    "Modern subjects retain recognisable structure.",
    "One dominant ink gesture controls each shot.",
    "Accent red occupies only a small focal role."
  ],
  "variation_axes": {
    "ink_intensity": {"type": "number", "min": 0.35, "default": 0.65, "max": 0.9},
    "realism": {"type": "enum", "values": ["graphic", "balanced", "cinematic"], "default": "balanced"}
  },
  "palette": {
    "paper": ["#EEE8DC"],
    "neutral": ["#111111", "#5B5B58", "#B9B3A9"],
    "accent": ["#A52A1F"],
    "forbidden": ["neon cyan", "neon magenta"]
  },
  "materials": ["visible rice-paper fibres", "wet-edge pooling", "dry-brush contour"],
  "composition": {"space": "preserve breathing room", "depth": "foreground/midground/background", "focus": "one dominant subject"},
  "subject_treatment": {"people": "recognisable silhouette and face", "objects": "preserve engineered geometry", "architecture": "ink mass plus controlled linework", "environment": "atmospheric wash"},
  "camera_language": {"movement": "one restrained move per shot", "perspective": "use directional perspective when narratively useful"},
  "motion_grammar": {"formation": ["water trace", "diffusion", "pigment pooling", "contour lock"], "subject": ["grounded natural motion"], "transition": ["brush sweep", "capillary spread"], "settle": "stop random diffusion after contour lock"},
  "negative_constraints": ["anime", "plastic 3D", "uniform digital blur", "fake Chinese text"],
  "generator_adapters": {},
  "fallbacks": ["Replace complex diffusion with a directional brush reveal plus edge pooling."]
}
```
