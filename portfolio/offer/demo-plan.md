# Rights-Safe Demonstration Plan

Status: **blocked until the source build and rights gates in `readiness-audit.md` pass**.

## Demonstration outcome

Show how one synthetic applicant record moves from intake to a human-reviewed exception queue and a redacted operational summary. The demo proves workflow design and failure handling, not customer results.

## Synthetic scenario

- Fictional agency: Northstar Staffing Lab.
- Fictional applicant and contact details from reserved example domains/numbers.
- Workflow: application submitted → required-field/document check → human approval queue → approved status notification draft → operational run record.
- Injected exception: missing work-authorization answer or an unsupported resume type.
- Human decision: qualification, rejection, hiring, and message sending remain outside automation.

## Five-minute script

1. State that all data and results are synthetic.
2. Show the current manual workflow map and modeled baseline assumptions.
3. Submit the synthetic intake.
4. Show validation, deduplication, and the exception path.
5. Approve one safe status transition manually.
6. Show the run ledger, alert/dead-letter record, retained fields, and deletion control.
7. Compare the run to the modeled baseline, clearly labeling it as a test—not a customer outcome.
8. End on the $750 diagnostic CTA.

## Acceptance gates

- Ownership/reuse decision recorded.
- Clean build and automated tests pass from a fresh environment.
- No customer source, secrets, production infrastructure, personal data, logos, or testimonials appear.
- Synthetic fixtures are deterministic and visibly labeled.
- Duplicate inputs do not create duplicate records or messages.
- Injected failure reaches a dead-letter record and one actionable alert.
- Logs and screenshots contain no unnecessary personal or credential data.
- Data deletion and environment teardown are demonstrated.
- Public use is explicitly approved.
