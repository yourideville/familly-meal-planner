---
description: Frontend React and TypeScript architecture rules
applyTo: frontend/src/**/*.{ts,tsx}
---

# Frontend React and TypeScript Rules

## Language Requirements
- All code (variable names, function names, types, interfaces, imports, comments) must be in **English**.
- Only user-facing text strings (labels, button text, error messages displayed to users) should be in **French**.
- Extract French UI strings into constants in `constants/` or dedicated locale modules for maintainability.


- Keep UI text/constants shared in dedicated modules (for example weekday labels in `constants/`), not duplicated in pages.
- Keep components focused: page components orchestrate data and compose UI; reusable rendering logic moves to shared components/hooks.
- Prefer typed domain contracts from `types/` and avoid inline ad-hoc object shapes.
- Handle async failures with explicit user-facing messages and avoid silent catches.
- Avoid premature optimization; add memoization only when re-render hotspots are observed.
- Keep accessibility basics: semantic elements, labels for form fields, and meaningful button text.
