---
description: Backend FastAPI architecture and API contract rules
applyTo: backend/**/*.py
---

# Backend FastAPI Architecture Rules

## Language Requirements
- All code (variable names, function names, class names, docstrings, comments) must be in **English**.
- UI strings in error messages can be in French for user-facing display, but internal logic and field names must be English.


- Keep router modules thin: validate HTTP concerns and delegate business behavior to services.
- Keep stateful and domain logic in `app/services/` and avoid cross-router duplication.
- Validate API invariants close to boundaries and return explicit HTTP status/detail for failures.
- Keep response models explicit and aligned with schema types in `app/schemas/`.
- Prefer deterministic service behavior for testability (resettable in-memory state, predictable outputs).
- Add or update tests when changing routing, validation, or menu generation behavior.

## Storage Abstraction
- `BACKEND_PERSISTENCE_MODE` env var controls the storage backend: `inmemory` (default) or `dynamodb`.
- `boto3` must only be imported when `BACKEND_PERSISTENCE_MODE=dynamodb` to avoid import failures locally.
- All DynamoDB I/O is gated behind `_USE_DYNAMODB` checks in the store module.
- Tests always run against in-memory storage.

## Admin Authentication
- Single shared password, no per-user accounts.
- Acceptable for a family-only application — do not over-engineer auth.
