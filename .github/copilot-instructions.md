# Copilot Instructions

> These instructions are automatically given to GitHub Copilot (coding agent,
> code review, and chat) for every task in this repository. Keep this file
> short, factual, and current. Replace the bracketed placeholders.

## What this project is

[One or two sentences: what the app/service does and who uses it.]

- **Primary language(s):** [e.g. TypeScript, Python]
- **Framework(s):** [e.g. Next.js 15, FastAPI]
- **Package manager:** [e.g. pnpm, uv, poetry]

## How to build, test, and lint

Always run these before considering a change complete. Match the exact commands.

```bash
# Install dependencies
[e.g. pnpm install]

# Build
[e.g. pnpm build]

# Run the full test suite
[e.g. pnpm test]

# Lint and format (fix before committing)
[e.g. pnpm lint && pnpm format]

# Type-check
[e.g. pnpm typecheck]
```

A change is not done until build, tests, lint, and type-check all pass.

## Coding standards

- Follow the existing style in the file you are editing; do not reformat
  unrelated code.
- [e.g. Use functional components and hooks; no class components.]
- [e.g. Prefer named exports.]
- [e.g. All new code must have unit tests.]
- [e.g. Use TypeScript strict mode; no `any` without a comment justifying it.]
- Keep public APIs documented. Update docs when behavior changes.

## Project structure

- `[src/]` — [application code]
- `[tests/]` — [tests]
- `[docs/]` — [documentation]
- [Add the few directories an agent most needs to know.]

## Things to avoid

- Do not commit secrets, tokens, or `.env` files.
- Do not edit generated files: [e.g. `*.generated.ts`, `dist/`, lockfiles unless deliberately bumping deps].
- Do not introduce new dependencies without justification in the PR description.
- Do not change CI workflow files unless the task is explicitly about CI.

## Pull request expectations

- Keep PRs small and focused on a single concern.
- Write a clear description: what changed, why, and how it was tested.
- Reference the issue being addressed.
