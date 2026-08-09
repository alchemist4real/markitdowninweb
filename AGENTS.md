# AGENTS.md — Workspace Design System & Behavioral Guardrails

## 🎨 Color Palette (Strict 2-Color Monochromatic Rule)
- **Vanilla (`#FFEBAF`)**: Main canvas background, card base fills, light mode highlights.
- **Moonstone (`#4C9DB0`)**: Main brand text, serif titles, icons, tab pills, button borders, active indicators, and specular shadow glints.
- **Strict Prohibition**: **ZERO** black (`#000000`/`#0D0D0D`), **ZERO** white (`#FFFFFF`), **ZERO** green (`#22C55E`), **ZERO** gradients, and **ZERO** extra colors.

---

## 🔤 Typography Rules
- All `markitdowninweb` title headers (`.logo-text`, `.brand-display`, `.brand-sub`, `.brand-main`) **MUST** use `Cormorant Garamond` serif font (`'Cormorant Garamond', Georgia, serif`).
- Interface controls, buttons, metadata, metrics, and logs use `DM Mono` (`'DM Mono', monospace`).
- No light/dark theme toggle buttons; single unified monochromatic experience.

---

## 💧 Apple WWDC 2025 Liquid Glass UI Material System
- **Optical Lensing**: `backdrop-filter: blur(28px) contrast(125%) brightness(108%) saturate(190%)`.
- **4-Point Specular Rim Refraction**:
  - `inset 0 2px 4px rgba(255, 255, 255, 0.95)` (Top rim light)
  - `inset 0 -3px 8px rgba(76, 157, 176, 0.35)` (Bottom shadow refract)
  - `inset 3px 0 6px rgba(255, 255, 255, 0.65)` & `inset -3px 0 6px rgba(76, 157, 176, 0.25)` (Side specular edges)
- **Mouse-Following Refraction**: Real-time cursor coordinate tracking (`--mouse-x`, `--mouse-y`) updating focal radial gradients via `initLiquidGlassEngine()`.
- **Fluid Ripples**: Expanding `.liquid-ripple` touch/click waves across glass surfaces.
- **SVG Displacement Lensing**: Real-time SVG `<filter id="liquidLens">` with `feTurbulence` and `feDisplacementMap`.

---

## 📐 Layout Symmetry & Credits
- Hero headers, input tabs, preset pills, and matrix nodes **MUST** be center-aligned for horizontal balance.
- Web footers and `README.md` **MUST** credit **Microsoft MarkItDown** (`github.com/microsoft/markitdown`) and **alchemist4real** (`github.com/alchemist4real`).
