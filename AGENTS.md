# AGENTS.md — Workspace Design System & Behavioral Guardrails

## 🎨 Color Palette (Strict 2-Color Monochromatic Rule)
- **Electric Yellow (`#FFE500`)**: Main canvas background, card fills, and inverted hover text.
- **Deep Indigo (`#362486`)**: Main brand text, Y2K titles, icons, tab pills, button borders, active indicators, and solid 3D shadows (`box-shadow: 4px 4px 0px #362486`).
- **Strict Prohibition**: **ZERO** black (`#000000`), **ZERO** white (`#FFFFFF`), **ZERO** green (`#22C55E`), **ZERO** extra colors.

---

## 🔤 Typography Rules
- All `markitdowninweb` title headers (`.logo-text`, `.brand-display`, `.brand-sub`, `.brand-main`) **MUST** use `Moonbase Alpha` Y2K font stack (`'Silkscreen', 'Micro 5', 'DotGothic16', 'Rubik Microbe', 'DM Mono', monospace`) and custom vector SVG letterforms in `logo.svg`.
- Interface controls, buttons, metadata, metrics, editor, preview, and logs use `DM Mono` (`'DM Mono', monospace`).
- Single unified 2-color monochromatic design system.

---

## ⚡ Clean OG Minimal Design System (Reverted from Liquid Glass)
- **Flat Bold Cards**: 2px solid Deep Indigo (`#362486`) borders with crisp 3D drop-shadows (`box-shadow: 4px 4px 0px #362486`).
- **High Legibility**: 10.5:1 WCAG AAA contrast ratio.
- **Single File Bundle**: All HTML, CSS, and JS bundled in `public/index.html`.

---

## 📐 Layout Symmetry & Credits
- Hero headers, input tabs, preset pills, and matrix nodes **MUST** be center-aligned for horizontal balance.
- Web footers and `README.md` **MUST** credit **Microsoft MarkItDown** (`github.com/microsoft/markitdown`) and **alchemist4real** (`github.com/alchemist4real`).
