## Name
Commit changes

## Description
Analyze the current repository state, group changes by goal, and create one or multiple clear conventional commits (with Gitmoji). Ask for a short human summary when needed.

## Parameters
- **message_hint** (string, optional): Short description of what you changed (e.g. "init backend + cdk"). Used to refine the commit message.

## Command
1. Run `git status` to see staged and unstaged changes.
2. Run `git diff` to inspect modifications.
3. Run `git log --oneline -10` to align message style.
4. If there are **no changes** (clean working tree), stop and say there is nothing to commit.
5. If there are changes, classify them by **goal** (feature, fix, docs, refactor, chore, test, infra, etc.).
6. Decide commit strategy:
   - If all files support one clear goal, create **one commit**.
   - If files represent distinct goals, create **multiple commits**.
   - Never mix unrelated goals in the same commit.
7. For each commit group:
   - Stage only relevant files (`git add <paths...>`). Prefer targeted adds over `git add .`.
   - Derive a concise title (max ~60 chars), using verbs like `init`, `add`, `update`, `fix`, `refactor`, `docs`, `chore`.
   - Use Gitmoji in all commit titles (e.g., ✨ feature, 🐛 fix, ♻️ refactor, 📝 docs, 🔧 chore, ✅ tests, 🚀 infra/deploy).
   - Include a brief body only when it adds useful context (the why, trade-offs, follow-up notes).
8. Create each commit using:

```bash
git commit -m "$(cat <<'EOF'
<COMMIT_TITLE>

<OPTIONAL_COMMIT_BODY>
EOF
)"
```

9. After all commits, run `git status` again:
   - If clean, confirm success and list commit hashes/titles.
   - If remaining files exist, explain what is left and why it was excluded.

## Examples
- Initial project structure:
  - Title: `✨ init project structure`
  - Body: `Set up backend, frontend, infra, and docs scaffolding.`
- Infra change:
  - Title: `🚀 switch infra to aws cdk`
  - Body: `Replace SAM layout with CDK app scaffold for Lambda and DynamoDB.`
- Mixed changes split by goal:
  - Commit 1: `✨ add voting endpoint and menu generation`
  - Commit 2: `📝 update local setup and API usage docs`