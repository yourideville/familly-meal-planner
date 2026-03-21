---
description: Backend FastAPI architecture and API contract rules
applyTo: backend/**/*.py
---

# Backend FastAPI Architecture Rules

- Keep router modules thin: validate HTTP concerns and delegate business behavior to services.
- Keep stateful and domain logic in `app/services/` and avoid cross-router duplication.
- Validate API invariants close to boundaries and return explicit HTTP status/detail for failures.
- Keep response models explicit and aligned with schema types in `app/schemas/`.
- Prefer deterministic service behavior for testability (resettable in-memory state, predictable outputs).
- Add or update tests when changing routing, validation, or menu generation behavior.
