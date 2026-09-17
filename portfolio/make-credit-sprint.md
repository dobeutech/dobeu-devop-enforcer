# Make Credit Sprint

The user-supplied screenshot shows 133,003.65 of 240,000 Make credits remaining and a 29-day reset window. The exact reset date, plan price, and Make credit accounting still need verification in the billing page.

## Guardrails

- Each scenario must have an owner, durable destination, idempotency key, retry limit, dead-letter path, kill switch, credit cap, and acceptance test.
- Store metadata and approved summaries, not secrets, raw credentials, unnecessary personal data, or unreviewed customer content.
- Drafting and research can be automated. External messages, production writes, purchases, cancellations, repository archival, and customer-data migrations require explicit approval.
- Start each scenario with synthetic data, then a small replay, then a bounded schedule.
- An expiring credit is not a reason to run low-value or risky operations.

## Priority allocation caps

These percentages are maximum experiment envelopes, not consumption targets. Reallocate only after the prior workflow passes its acceptance test.

| Priority | Scenario | Durable output | Cap on current remaining credits | Acceptance test |
|---:|---|---|---:|---|
| 1 | Subscription and capacity oversight | Daily cost/credit snapshot plus renewal alerts | 5% | Alert fires from test threshold; no credential values stored |
| 2 | Repository portfolio refresh | Versioned metadata delta, risk queue, and ownership gaps | 20% | Repeat runs create no duplicates and surface only changed records |
| 3 | Staffing diagnostic intake | Qualified intake record, pain baseline, approval-ready scope draft | 20% | Synthetic lead completes intake-to-draft path with validation and opt-out |
| 4 | Engineering-memory ingestion | Accepted artifact, provenance, summary, tags, and embedding job record | 25% | Same artifact is deduplicated and retrievable with source attribution |
| 5 | Delivery monitoring and outcome report | Failure alert, run record, and before/after report inputs | 15% | Injected failure reaches dead-letter path and creates one actionable alert |
| 6 | Reserve for replay and the best-performing workflow | Controlled additional run capacity | 15% | Released only after a measured accepted outcome |

## Build order

1. Verify reset date, credit-unit accounting, scenario history, and cash price; record them in `cost-map.json`.
2. Build a reusable scenario shell: webhook/schedule, validation, idempotency, run ledger, capped retries, dead-letter record, alert, and kill switch.
3. Implement the subscription/capacity digest first because it governs every later run.
4. Add portfolio metadata deltas; do not fetch entire repository contents on every schedule.
5. Add staffing diagnostic intake with synthetic inputs and a human approval step before any customer-facing action.
6. Add memory ingestion only for accepted artifacts; keep source pointers and retention class.
7. Run failure injection and replay tests, then allocate remaining capacity to the workflow with the strongest accepted-output evidence.

## Daily oversight prompt

The digest should answer only actionable questions:

- Which allowance or renewal is approaching a boundary?
- Which paid tool had no accepted outcome in the current review window?
- Which workflow is blocked and what is the smallest approval needed?
- Which accepted artifact is not yet stored in engineering memory?
- Which revenue-stage action is due today?

If none apply, the digest should say so and avoid generating work.
