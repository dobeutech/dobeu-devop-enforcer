# Revenue Asset Readiness Audit

Observed from the public source on 2026-09-11. GitHub MCP repository reads returned insufficient scope, so this audit used read-only public GitHub source as the fallback. It is a targeted launch audit, not a full security assessment.

## Decision

The **Staffing Operations Automation Diagnostic** can be sold now as a professional service using manual intake, signed scope, and provider-hosted/manual invoicing. Neither audited repository should currently be presented as a production-ready reusable product or trusted for integrated checkout.

## `unique-staffing-prof`

Useful evidence:

- Staffing-specific applicant intake, resume upload, Supabase migrations, admin workflow, analytics, and API documentation exist.
- The implementation provides concrete workflow vocabulary for a credible staffing diagnostic.
- The repository is MIT licensed, but the license notice names GitHub, Inc. and the application is customer-specific; ownership, customer rights, branding, data, and reusable-code boundaries still require confirmation.

Launch blockers:

- `src/components/EnhancedApplyForm.tsx` declares `trackingData` twice in the same component, a compilation blocker.
- `package.json` has no test command and the repository contains no demonstrated application test suite.
- The repository's own `.docs/IMPLEMENTATION_STATUS.md` says the testing framework, MFA, error tracking, and uptime monitoring were not started and the jobs database migration still required execution. Some documentation may now be stale, so each claim requires runtime evidence.
- Applicant data and resumes are sensitive. A demo must use synthetic data, isolated infrastructure, explicit retention, least privilege, and a tested deletion path.
- Generated Netlify state is committed and the shallow checkout is unusually large; generated deployment artifacts should not become the reusable product baseline.

Go/no-go:

- **Go:** use workflow patterns and rights-safe screenshots or a repaired synthetic demo as supporting proof.
- **No-go:** reuse customer data, imply measured customer results, deploy for another customer, or expose a live applicant system before rights, build, tests, and security gates pass.

## `dobeucloud`

Useful evidence:

- Quote intake, invoice models, administrative views, PayPal/Square routes, analytics, and a client dashboard foundation exist.
- The repository can become the canonical sales and delivery surface after a focused repair.

Launch blockers:

- There is no test suite in the repository.
- The contact form contains a TODO instead of a persistent submission, and scheduling uses random mock availability before returning a success message.
- PayPal order creation accepts the amount from the browser instead of loading an immutable server-side invoice or price. Square likewise accepts amount and location input from the request.
- The payment-record route trusts browser-supplied transaction status and amount rather than verifying a signed provider event and enforcing idempotency.
- Unauthenticated quote intake can assign a MongoDB `ObjectId` field from a Supabase UUID/contact identifier, and the server route does not apply the client-side Zod contract.
- The quote notification calls an `/api/emails/send` route that is absent from the repository tree.
- Marketing copy claims 24/7 support and a 100% money-back guarantee without evidence of staffing, terms, or operational coverage.

Go/no-go:

- **Go:** use the offer language in this pack on an approved simple page and use a reputable provider-hosted invoice/payment link tied to the agreed diagnostic.
- **No-go:** enable the current custom checkout, scheduling confirmation, guarantee, or 24/7 claim until server-side verification, tests, policies, and operational ownership pass review.

## Minimum repair before integrated launch

1. Confirm ownership, customer rights, and which source repository is canonical.
2. Remove unsupported claims and collapse the site to one buyer, one problem, one offer, and one CTA.
3. Validate all quote/intake data on the server, rate-limit abuse, minimize retained data, and escape notification content.
4. Bind checkout to a server-owned offer/invoice and amount; verify provider signatures/events; enforce idempotency and reconciliation.
5. Replace mocked contact/scheduling success paths with real, monitored integrations or remove them.
6. Add unit, integration, authorization, payment-replay, failure-path, and end-to-end conversion tests.
7. Prove deployment, monitoring, backup, rollback, privacy, terms, and incident ownership in an isolated environment.
