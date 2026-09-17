# CLAUDE.md

> Project guide for Claude Code (terminal, GitHub Action, and PR review).
> Keep it lean and current — every line is read on each run. Replace the
> bracketed placeholders.

## Project overview

[One or two sentences: what this project does.]

- **Stack:** [languages, frameworks, package manager]
- **Entry points:** [e.g. `src/index.ts`, `app/main.py`]

## Commands

Run these to validate any change. Use the exact commands.

```bash
[install]      # e.g. pnpm install
[build]        # e.g. pnpm build
[test]         # e.g. pnpm test
[lint]         # e.g. pnpm lint
[typecheck]    # e.g. pnpm typecheck
```

**Definition of done:** build + tests + lint + typecheck all pass. Run them
before committing or opening a PR.

## Code style and conventions

- Match the style of the file you're editing; don't reformat unrelated lines.
- [e.g. TypeScript strict; avoid `any`.]
- [e.g. Tests live next to source as `*.test.ts`; cover new branches.]
- [e.g. Conventional Commits for commit messages.]

## Architecture notes

- `[src/]` — [what lives here]
- `[tests/]` — [test layout]
- [Any non-obvious patterns an agent should respect.]

## Guardrails

- Never commit secrets or `.env` files.
- Don't edit generated files or lockfiles unless that's the task.
- Don't add dependencies without noting why in the PR description.
- Ask (in a PR comment) before large refactors or schema/migration changes.

## When responding to @claude

- Keep PRs small and focused.
- Explain what changed, why, and how you verified it.
- If a request is ambiguous, state your assumption and proceed, or ask.
