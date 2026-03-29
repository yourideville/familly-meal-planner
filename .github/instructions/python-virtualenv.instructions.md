---
description: Local Python virtual environment activation guidance
applyTo: **/*.py
---

# Python Virtual Environment Rules

- Before running any Python command, tests, or packaging step, activate the local Python virtual environment.
- Use the explicit repository venv activation command:
  - `source /home/youri/Projects/Sources/.venv/bin/activate`
- If `activate-python` is configured in the shell, it may also work, but prefer the explicit `source` command.
- Use the activated environment for both backend and CDK dependency installation.
- Do not run Python commands directly against the system Python unless the virtual environment is unavailable.
- Keep dependency installation scoped to the venv and avoid global package pollution.
