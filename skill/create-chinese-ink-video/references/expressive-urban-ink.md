# Expressive Urban Ink

Use this profile for the B direction in `assets/expressive-urban-ink-reference-grid.png`: a high-contrast, contemporary urban ink language with strong perspective, wet pavement, calligraphic black masses and restrained cinnabar accents. Treat the reference as visual evidence, not content to copy.

## Style family

The reference grid contains related but distinct branches:

| Branch | Character | Best use |
|---|---|---|
| A — literati minimal | Large negative space, calm red sun, restrained subject | Brand pause, ending, premium calm |
| B — expressive urban | Aggressive black strokes, deep perspective, rain reflections | Narrative, mobility, city energy |
| C — architectural linework | Ordered ink drawing, pale wash, formal stability | Architecture, real estate, corporate |
| D — mist noir | Atmospheric grey wash, cinematic realism | Struggle, history, drama |
| E — calligraphic infrastructure | Circular brush gesture, graphic construction | Migration, transit, conceptual transitions |
| F — ink and gold monument | Gold accent, iconic architecture, ceremonial scale | Luxury, finance, landmarks |

Keep B as the base profile. Do not average all six branches. Borrow another branch only as an explicit variation axis or shot-level exception.

## Visual thesis

Build a recognisable contemporary world from wet ink deposits and decisive calligraphic motion. Preserve rice-paper breathing room and realistic subject structure while allowing black ink to carry speed, pressure and emotion.

## Core invariants

1. Keep warm off-white rice paper visibly present.
2. Preserve recognisable modern geometry in vehicles, people and architecture.
3. Give every shot one dominant directional ink gesture.
4. Use black, grey and paper as the main field; reserve cinnabar red for a small narrative focal role.
5. Combine wet diffusion for atmosphere with dry contour or precise detail for structural lock.
6. Let ink behavior support composition or narrative; never add splatter as decoration alone.

## Variation axes

- **Ink intensity**: restrained 0.35, balanced 0.65, forceful 0.90.
- **Realism**: graphic, balanced, cinematic.
- **Density**: spacious, centered, immersive.
- **Atmosphere**: dry daylight, mist, wet street, storm pressure.
- **Accent**: none, cinnabar, muted gold. Do not combine strong red and gold without approval.
- **Gesture**: horizontal sweep, vanishing-point pull, vertical fall, circular enclosure.

Default to balanced realism, 0.65 ink intensity, centered density, wet-street atmosphere, cinnabar accent and vanishing-point pull.

For the approved strong B2 variant, use ink intensity 0.82–0.88, balanced-to-graphic realism, broad carbon-black clothing or object masses, visible flying-white scratches and sparse burnt orange-red accents. Keep faces readable with 2–3 wash planes plus contour; do not retain photographic pores. Use this variant when the user explicitly asks to match the forceful texture of a vehicle or urban-ink reference.

## Color and tone

- Paper: warm ivory, not pure white.
- Ink: near-black, charcoal, smoke grey and pale wash.
- Accent: sparse cinnabar on tail lights, seals, a garment detail or a single story object.
- Reflection: use muted red only where a physical or narrative source exists.
- Avoid neon cyan/magenta, broad saturated fields, colorful cyberpunk lighting and uniform sepia filters.

## Subject treatment

- **People**: retain face, hands, pose and clothing silhouette. Use wash in secondary clothing areas; lock face and gesture with controlled linework.
- **Strong B2 people**: preserve identity, glasses, gaze, hand anatomy and tool position; simplify skin into controlled washes and turn workwear into broad dry-brush black masses.
- **Vehicles/products**: preserve proportions, mechanical joins and brand-neutral geometry. Form with contour stroke, underside pooling and selective reflections.
- **Architecture**: establish pale wash mass, then structural lines, then limited deep-ink accents. Do not dissolve every edge.
- **Environment**: use wet-on-wet wash, atmospheric depth and paper gaps. Keep distant layers lighter.
- **Text/Logo**: composite supplied assets deterministically. Do not ask an image model to invent legible Chinese text or marks.

## Ink formation grammar

Use:

```text
water trace
→ capillary spread
→ pigment deposit and wet-edge pooling
→ dry-brush or linework contour lock
→ restrained accent
→ settle
```

Match technique to subject:

| Element | Formation |
|---|---|
| Sky, fog, distant city | Wet wash and pale diffusion |
| Road and reflection | Directional water trace and dragged ink |
| Building | Wash mass, structural line, selective pooling |
| Person, vehicle, product | Contour stroke, interior deposit, detail lock |
| Tree, smoke, cloud | Broken ink, bloom and dry-brush interruption |
| Accent | Cinnabar point, short reflection or one seal-like landing |

Do not reveal a finished frame with a smooth radial mask. Diffusion must show paper-controlled irregularity, wet-edge concentration and pigment granulation. After contour lock, stop random melting.

## Motion budget

Use approximately:

- 70% stable narrative structure
- 20% ink material behavior
- 10% memorable accent or exceptional gesture

Treat this as attention and risk allocation, not a pixel or duration formula.

Per shot:

- Use one primary ink event.
- Use one dominant camera behavior.
- Avoid simultaneous strong camera, subject and ink motion.
- Follow a dense ink shot with visual breathing room.
- Do not repeat “one drop blooms into the whole scene” across consecutive shots.

## B-style proof shot

```text
Paper fibre and a faint water trace appear
→ pale ink follows the road vanishing point
→ distant skyline deposits from grey wash
→ dry contours lock the main towers
→ a black vehicle enters with grounded motion
→ side brush masses sweep in along perspective
→ cinnabar tail lights create one short wet reflection
→ diffusion stops and the composed frame holds
```

## Negative constraints

- Anime, cartoon, oil painting or plastic 3D
- Generic “digital watercolor” blur
- Decorative splatter without compositional purpose
- Every edge dissolved
- Entire frame filled with black ink and no breathing room
- Fake Chinese characters, invented seals, watermarks or generated logos
- Red used as a broad fill instead of a focal accent
- Subject geometry changing during diffusion
- Continuous random ink motion after the scene is complete
