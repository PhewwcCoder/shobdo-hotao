---
name: frutiger-aero-ui
description: Design guidance for styling the ShobdoHotao PySide6/Qt app in the Frutiger Aero aesthetic — glossy glass, blue gradients, water/bubble highlights, early-2000s optimism. Use whenever building or restyling any UI in this app.
---

# Frutiger Aero UI Skill (ShobdoHotao)

## Aesthetic principles
- Era: early-to-mid 2000s "Frutiger Aero" — glossy, optimistic, clean, nature-meets-tech.
- Mood: a noise-free, calm, sunlit-underwater world. Tranquil, not busy.
- Core motifs: glass/gloss surfaces, soft blue gradients (sky blue → deep aqua),
  water droplets, soap bubbles, subtle white light reflections, rounded shapes.

## Color palette
- Primary blues: #6CC4F5, #2E9BE0, #1B6FB3
- Deep background: #0B1622 to #16263B (dark navy, like deep water)
- Glass white highlights: rgba(255,255,255,0.6) sheens on top edges
- Accent glow: soft white/cyan bloom

## Buttons (old-Windows / Aqua glass style)
- Rounded corners (10–16px radius).
- Vertical gradient: lighter at top, darker at bottom (glossy).
- A bright highlight band across the TOP HALF (the classic "Aqua" glass sheen).
- Subtle outer glow / soft shadow.
- Hover: brighten and slightly enlarge the sheen (dynamic feel).
- Implement with Qt stylesheets (QSS) using qlineargradient. No external images
  unless explicitly required.

## Glass bubble image containers
- Decorative images sit INSIDE translucent glass spheres (like soap bubbles).
- The bubble: circular, semi-transparent, with a bright highlight near top-left
  and a soft rim light. The image inside is faint/low-opacity.
- Position bubbles at slightly off-kilter / awkward angles for a dreamy,
  "different world" feel — not perfectly aligned to the grid.

## Layout rules
- Keep it tasteful and uncluttered — Frutiger Aero is clean, not maximalist.
- Generous spacing, centered focal content.
- Respect the existing i18n/Translator system for ALL text (Bengali + English).

## Hard constraints
- Always use PySide6/Qt-native widgets and QSS.
- Never break the existing Bangla|EN toggle or existing functionality.
- Do not modify Stage 2 / SQLite code.