# First Revenue Motion: Staffing Operations Automation Sprint

## Expert decision

Sell a productized staffing-operations service before building another standalone SaaS product.

- Use `unique-staffing-prof` only as rights-safe domain proof after its compile, test, data, and customer-rights gates pass.
- Treat `dobeucloud` as the future single company sales/delivery surface, but do not use its mocked scheduling, unimplemented contact path, unsupported claims, or current custom payment endpoints for launch.
- Launch the diagnostic with an approved minimal form and verified provider-hosted/manual invoice before repairing the larger sales platform.
- Use Make and Supabase for bounded customer automations where they reduce a measured manual workflow.
- Keep customer-specific code and data rights separate. Reuse patterns, schemas, runbooks, and anonymized proof only when contracts permit it.

## Offer

**Buyer:** owner or operations leader at a small staffing agency with manual applicant intake, qualification, status updates, document routing, scheduling, or reporting.

**Promise:** identify the highest-cost staffing workflow and put one bounded automation into production within one week, with monitoring, a manual fallback, and a runbook.

**Price tests:**

- Paid diagnostic: $500–$1,000; first target $750.
- Bounded implementation: $1,500–$3,000; first target $2,000.
- Managed monitoring/upkeep: $250–$750/month; first target $400/month.

The year-one base case is three $750 diagnostics, two $2,000 implementations, one $400 retainer for ten months, and one $2,000 engineering-memory diagnostic: $12,250 collected revenue against a $7,776 annual software ceiling.

## Current state

Completed internally: portfolio ranking, source readiness audit, offer/pricing copy, intake contract, deterministic qualification, diagnostic/SOW/outcome templates, subscription controls, and evidence-based revenue reporting.

Still required for launch: owner approval of the offer and terms, a verified provider-hosted/manual payment path, customer-rights decision, minimal publication destination, prospect research, and send approval. Existing application code is not the critical path to collecting the first diagnostic payment.

## Fourteen-day internal launch backlog

| Order | Internal task | Output | Acceptance evidence | Approval boundary |
|---:|---|---|---|---|
| 1 | Verify ownership, licenses, customer rights, live deployment, domains, and data classification for `unique-staffing-prof` | Rights/dependency decision record | Named owner and explicit reusable/anonymized boundary | Customer/legal approval if required |
| 2 | Reproduce the applicant workflow in an isolated environment with synthetic data | Demo run and failure log | One complete synthetic applicant path and no production access | No production data |
| 3 | Select one measurable workflow pain | Diagnostic worksheet | Baseline minutes, handoffs, error/miss rate, owner, and estimated value | Customer confirmation later |
| 4 | Publish the approved offer through the smallest safe surface | Focused landing page and diagnostic application | One buyer, pain, promise, proof boundary, price, form, and verified hosted/manual invoice | Copy, terms, destination, and publication require approval |
| 5 | Create diagnostic, SOW, security/data questionnaire, runbook, and before/after report templates | Versioned delivery kit | Scope, exclusions, acceptance, rollback, credential boundary, and support window present | Contract review before use |
| 6 | Build a rights-safe demonstration from synthetic or explicitly approved evidence | Five-minute demo script and screenshots | No customer secrets/PII; measurable before/after story | Public use requires approval |
| 7 | Build a qualified list of 25 staffing agencies with one observed workflow signal each | Prospect research table | Named buyer role, source, problem hypothesis, and exclusion reason | No outreach yet |
| 8 | Draft three outreach variants and follow-up sequence | Approval-ready drafts | Specific pain/evidence, paid diagnostic ask, opt-out, no fabricated claim | Sending requires approval |
| 9 | Configure the internal funnel and revenue ledger | Stages and dashboard definition | Lead → call → paid diagnostic → implementation → retainer; only evidenced settled payments count | CRM writes require selected system |
| 10 | Run the launch-readiness review | Go/no-go packet | Rights, demo, offer, delivery capacity, pricing, payment, support, and outreach gates pass | Human go-live decision |

## Stop rules

- Do not publish or contact prospects until ownership, proof, delivery, and approval gates pass.
- Do not build a feature unless a paid diagnostic requires it or it is a reusable safety/delivery control.
- Do not claim the existing staffing implementation produced results without customer-approved measurements.
- If ten interviews produce no repeated paid pain, change buyer/problem before changing technology.
- If delivery cannot reach positive gross margin, narrow scope or stop the offer rather than subsidizing it with subscription credits.
