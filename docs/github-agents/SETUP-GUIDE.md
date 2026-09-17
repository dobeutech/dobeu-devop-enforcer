# GitHub Cloud Agents — Setup & Best Practices

This kit sets up three kinds of GitHub cloud agent, with security-first defaults.

## Files in this kit

- `.github/copilot-instructions.md` — steers GitHub Copilot (coding agent, review, chat)
- `.github/workflows/copilot-setup-steps.yml` — pre-installs deps in Copilot's agent env
- `.github/workflows/claude.yml` — interactive @claude agent (issues/PRs)
- `.github/workflows/claude-code-review.yml` — automatic Claude review on every PR
- `.github/workflows/agent-issue-triage.yml` — event-driven CI agent: auto-labels new issues
- `CLAUDE.md` — project guide for Claude Code

## Account-side steps (only the repo owner can do these)

1. **Copilot coding agent:** requires a qualifying Copilot plan; enable under
   Settings → Copilot → Coding agent.
2. **Claude Code:** install the Claude GitHub App (https://github.com/apps/claude)
   and add a repo secret `ANTHROPIC_API_KEY` (or `CLAUDE_CODE_OAUTH_TOKEN`).
   Easiest path: run `/install-github-app` from Claude Code in a terminal.

Until the `ANTHROPIC_API_KEY` secret exists, the Claude workflows will no-op /
fail on trigger — that is expected. Add the secret to activate them.

## Before merging

Fill in the bracketed placeholders in `copilot-instructions.md`, `CLAUDE.md`, and
`copilot-setup-steps.yml` with this repo's real stack and build/test/lint commands.

## Security defaults baked in

- Least-privilege `permissions:` per workflow.
- `concurrency` groups + `timeout-minutes` caps.
- Fork PRs can't access secrets (don't switch to `pull_request_target`).
- Pin actions; enable Dependabot for `github-actions`.
- Keep branch protection + CODEOWNERS so humans review agent output.
