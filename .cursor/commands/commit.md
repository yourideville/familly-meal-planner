## Name
Commit changes

## Description
Analyze the current repository state, summarize staged and unstaged changes, and create a clear, conventional git commit message. Ask for a short human summary when needed.

## Parameters
- **message_hint** (string, optional): Short description of what you changed (e.g. "init backend + cdk"). Used to refine the commit message.

## Command
1. Run `git status` to see staged and unstaged changes.
2. Run `git diff` to inspect modifications.
3. If there are **no changes** (clean working tree), stop and say there is nothing to commit.
4. If there are changes:
   - Derive a concise, descriptive commit title (max ~60 chars).
   - Include a brief body only when it adds real context (e.g. why a design was chosen).
   - Prefer verbs like `init`, `add`, `update`, `fix`, `refactor`, `docs`, `chore`.
5. Stage relevant files:
   - For first commit or small change: `git add .`.
   - Otherwise prefer targeted adds (e.g. `git add backend/ frontend/ infra/ docs/`).
6. Create the commit using:

```bash
git commit -m "$(cat <<'EOF'
<COMMIT_TITLE>

<OPTIONAL_COMMIT_BODY>
EOF
)"
```

7. After committing, run `git status` again to confirm a clean working tree (or show remaining untracked files).

## Examples
- Initial project structure:
  - Title: `init project structure`
  - Body: `Set up backend, frontend, infra, and docs scaffolding.`
- Infra change:
  - Title: `switch infra to aws cdk`
  - Body: `Replace SAM layout with CDK app scaffold for Lambda and DynamoDB.`