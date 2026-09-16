# Internal Foundation Readiness

Generated from snapshot: `dobeu-foundation-2026-09-16-reviewed-baseline` at 2026-09-16T10:44:36Z

Status: **foundation_slice_ready_for_review**

## Boundary

- External writes allowed: **false**
- Approved task: `foundation-first-slice`
- Excluded actions: connector reauthentication or scope expansion; production or customer-data writes; deployments and scenario runs; publication, contact enrichment, and outreach; billing changes; repository archival, transfer, or deletion

## Evidence coverage

- Public repositories: **87**
- Full company repository coverage: **false**
- Supabase projects observed/mapped: **4/0**
- Open evidence conflicts: **1**
- Baseline artifacts locked by hash: **7**

## Financial checkpoint

- Monthly software baseline: **$648**
- Annual software baseline: **$7776**
- Evidenced collected revenue: **$0**
- Minimum one-year goal: **$7777**
- Operating target: **$12000**

## Blocking evidence

| Type | ID | Status | Required action | Evidence |
|---|---|---|---|---|
| source | `github-public-portfolio` | partial | Private and organization-only repositories are not visible with the current GitHub MCP scope. | `portfolio/repositories.json` |
| source | `supabase-project-posture` | partial | Native project enumeration and repository, deployment, owner, backup, and data-class mappings are incomplete. | `portfolio/connector-status.json` |
| source | `make-credit-and-connection-observations` | conflict | The screenshot and connector snapshots do not agree on organization visibility; scenario history and rollover terms remain unknown. | `portfolio/cost-map.json#prepaid_capacity` |
| source | `subscription-cost-baseline` | partial | Invoices, renewal dates, commitments, account owners, and measured utilization are not yet reconciled. | `portfolio/cost-map.json` |
| project_mapping | `supabase-routeready` | unmapped | Assign canonical repository, deployment, data owner/classification, backup evidence, and cost. | `portfolio/connector-status.json` |
| project_mapping | `supabase-dobe-net` | unmapped | Assign canonical repository, deployment, data owner/classification, backup evidence, and cost. | `portfolio/connector-status.json` |
| project_mapping | `supabase-ikram-meme-and-co` | unmapped | Assign canonical repository, deployment, data owner/classification, backup evidence, and cost. | `portfolio/connector-status.json` |
| project_mapping | `supabase-dot-copilot` | unmapped | Assign canonical repository, deployment, data owner/classification, backup evidence, and cost. | `portfolio/connector-status.json` |
| conflict | `make-organization-visibility` | open | Run a new read-only account-scoped inventory and reconcile it to the billing screenshot before building or scheduling a scenario. | `portfolio/connector-status.json` |

## Closed approval boundary

| Gate | Class | Status | Decision required | Owner |
|---|---|---|---|---|
| G1 | access | not_requested | Expand or reauthenticate GitHub, Supabase, Make, Sentry, or other connector access. | workspace-owner |
| G2 | internal_pilot | not_requested | Provision the internal assistant database branch, retention policy, identities, and gateway keys. | security-data-owner |
| G3 | automation_write | not_requested | Enable any issue, comment, pull request, scenario, database, or deployment write. | system-owner |
| G4 | commercial_launch | not_requested | Publish the offer, enable payment collection, enrich contacts, or send outreach. | commercial-owner |
| G5 | billing | not_requested | Pause, downgrade, cancel, purchase, or replace a subscription. | billing-owner |
| G6 | repository_lifecycle | not_requested | Consolidate, archive, transfer, or delete a repository. | repository-owner |
| G7 | productization | not_requested | Offer a hosted external engineering-memory or governance product. | business-security-owner |

## Next slice

1. Review this foundation diff and keep G1 through G7 closed until their evidence packets are ready.
2. Request least-privilege GitHub repository/settings read scope and reconcile public, private, organization, archived, and transferred totals.
3. Collect a fresh account-scoped Make organization, team, scenario, execution-history, credit, reset, and rollover snapshot to resolve the open conflict.
4. Map all four Supabase projects to source, deployment, owner, data class, backup, and cost without reading application rows.
5. Persist and freshness-check the 25 organization-level staffing prospects with outreach_authorized=false.
6. Prepare G2 evidence before provisioning a Supabase branch or gateway credentials for the engineering-memory pilot.

This report is an internal readiness artifact. It is not permission to expand access, mutate an external system, contact a prospect, change billing, or alter repository lifecycle state.
