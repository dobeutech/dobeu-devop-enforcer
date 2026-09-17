# Revenue Portfolio Foundation

This directory turns the public GitHub portfolio into a repeatable, evidence-labeled revenue ranking. It is an internal decision aid, not a product-market-fit claim and not authorization to archive or delete repositories.

## Outputs

- `repositories-source.json`: public GitHub repository metadata captured by the refresh.
- `repositories.json`: normalized scores, decisions, cost-mapping state, evidence gaps, and annual revenue targets.
- `revenue-ranking.md`: generated human-readable ranking for all public repositories.
- `launch-backlog.md`: the first revenue motion and approval-gated delivery plan.
- `cost-map.json`: user-reported subscription costs, overlaps, evidence gates, and comparison bookends.
- `cost-actions.md`: the 48-hour, 7-day, 14-day, and 30-day consolidation decisions.
- `make-credit-sprint.md`: bounded workflows for turning expiring Make capacity into durable internal assets.
- `connector-status.json`: minimum, non-secret evidence about GitHub, Supabase, Make, and Composio coverage.
- `revenue-ledger.json`: canonical opportunity/payment ledger; only evidenced settled payments count as collected revenue.
- `revenue-ledger.schema.json`: portable validation contract for the canonical ledger.
- `revenue-dashboard.md` and `revenue-control.json`: generated separation of collected revenue, contracts, pipeline, and the remaining one-year gap.
- `revenue-ledger.csv`: empty interoperability header; it is not the canonical source.
- `templates/`: diagnostic, statement-of-work, outcome-report, and repository-retirement controls.
- `offer/`: conversion copy, source readiness audit, synthetic demo, intake contract, and deterministic qualification triage for the first paid offer.
- `launch-readiness.json`: explicit separation between internal readiness, human approvals, product-launch blockers, and collected-revenue proof.

## Refresh and validate

```bash
./portfolio/refresh.sh
./portfolio/refresh-revenue.sh
./portfolio/validate.sh
```

The refresh uses the public GitHub REST endpoint because the connected GitHub MCP identity currently returns `Insufficient scope` for repository enumeration and content reads. If `GITHUB_TOKEN` is supplied, it is used only as an authorization header and is never printed or persisted by the script.

## Scoring interpretation

Scores combine business value, time to revenue, differentiation, execution readiness, strategic leverage, and maintenance penalty. They rank the *next commercial action*; they do not measure code quality. Manual judgments and their rationale live in `config.json`, while GitHub metadata remains separately captured for auditability.

Direct repository cost is deliberately `null` until invoices, hosting projects, databases, domains, model/API usage, and customer workloads are mapped. Shared subscription cost must not be fabricated or divided evenly across repositories.

The cost map treats consumer AI subscriptions as interactive seats unless the provider explicitly permits automated/API use. A future gateway can route metered APIs and local models, while seat retention is decided through accepted outcomes per dollar and operator hour.

## Safety boundary

- No repository is deleted or archived automatically.
- Private and organization-only repositories are not represented until GitHub read scope is repaired.
- RouteReady appears as an evidence gap because its Supabase project/cost is known but no matching public source repository was found.
- Four Supabase projects are visible through a read-only Composio fallback, but all remain unassigned to canonical source until ownership and deployment evidence is reviewed.
- Make's connected fallback currently returns no visible organization, so the screenshot is the only credit evidence and no remote scenarios were changed.
- Traffic, customers, contracts, and payment evidence must be joined before any score is treated as validated demand.
- Generated artifacts and internal work never count toward the $7,777 collected-revenue completion gate.
