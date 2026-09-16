# Cost and Tool Consolidation Actions

The current user-reported baseline is **$648/month ($7,776/year)**. The first goal is not to consume every allowance; it is to turn paid capacity into accepted, reusable outputs and stop renewing overlapping capacity that has no distinct job.

## Immediate decision

Protect the engineering foundation while running two short comparisons:

1. Pick one primary interactive-AI seat through a 14-day outcome bakeoff. Use the same three tasks, acceptance rubric, and time tracking for Claude Max, OpenAI Pro, and any serious alternative. Copilot, Google AI, and Supagrok survive only if they own a distinct recurring task.
2. Pick at most one primary AI UI builder. Before changing v0, Figma, Lovable, Bolt, or Replit, export owned artifacts and identify live deployments, collaborators, and portability constraints.

Do not attempt to route consumer-plan allowances through an AI gateway unless the provider explicitly supports automated/API usage under that plan. The future gateway should route metered APIs and local models; this ledger should separately manage interactive seats.

## Decision windows

| Window | Decision | Required evidence | Safe action |
|---|---|---|---|
| 48 hours | Map every paid service to an owner, renewal date, export method, and active workstream | Invoice/plan record and named consumer | Disable auto-renew only where no commitment or live dependency exists |
| 7 days | Map Supabase/Vercel/RouteReady projects to canonical source and data ownership | Repo, deployment, domain, database, backup, customer, and rollback links | Quarantine unknowns; do not delete data or deployments |
| 14 days | Select the primary AI seat and UI builder | Accepted artifacts, operator minutes, rework, cash/API cost, and unique capability | Downgrade or pause reversible losers after export checks |
| 30 days | Review the remaining portfolio | Collected revenue, qualified pipeline, delivery use, and reliability | Retain, renegotiate, consolidate, or cancel with an owner and recovery record |

## Savings bookends

The protected technical foundation in `cost-map.json` is $74/month: Ona, GitHub organization controls, one Supabase Pro foundation, and Vercel. It is a comparison floor, not a blind recommendation.

- Foundation plus the $100 OpenAI reference seat: **$174/month**, a maximum comparison saving of **$474/month or $5,688/year** before RouteReady and any required specialist tool.
- Foundation plus the $200 Claude reference seat: **$274/month**, a maximum comparison saving of **$374/month or $4,488/year** before RouteReady and any required specialist tool.
- RouteReady adds $15/month only if the source, consumer, data owner, and isolation need validate retention.

Actual savings must be calculated from invoices and effective cancellation dates. Annual commitments, taxes, API charges, and Make's cash cost are still unknown.

## Outcome accounting

Every paid-agent task should eventually emit this minimal record into the memory system:

```json
{
  "task_id": "stable-id",
  "workstream": "staffing-automation-sprint",
  "tool_or_model": "provider-plan-or-model",
  "started_at": "RFC3339 timestamp",
  "operator_minutes": 0,
  "metered_cost_usd": null,
  "artifact_uri": "durable internal reference",
  "acceptance_status": "accepted|rework|rejected",
  "revenue_stage": "internal|lead|diagnostic|implementation|retainer|collected",
  "reviewer": "named human or approved evaluator"
}
```

Optimize for accepted outcomes per dollar and operator hour. Token volume, chats sent, and credits consumed are capacity measures, not business outcomes.
