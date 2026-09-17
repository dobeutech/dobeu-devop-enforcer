def count_by($field):
  group_by(.[$field])
  | map({key: .[0][$field], value: length})
  | from_entries;

def evidenced_revenue:
  [
    .[]
    | select(
        .status == "settled"
        and .collected_at != null
        and (.evidence_ref // "" | length) > 0
        and .unaffiliated_customer == true
      )
    | if .kind == "refund" then -.amount_usd else .amount_usd end
  ]
  | add // 0;

($repositories[0]) as $repos
| ($costs[0]) as $cost
| ($launch[0]) as $launch_state
| ($revenue[0]) as $revenue_state
| . as $state
| ([$state.sources[] | select(.status != "complete")]) as $incomplete_sources
| ([$state.projects[] | select(.mapping_status != "mapped")]) as $unmapped_projects
| ([$state.conflicts[] | select(.status == "open")]) as $open_conflicts
| ([$state.approvals[] | select(.status != "approved")]) as $pending_approvals
| {
    schema: "readiness-report/v1",
    generated_from_snapshot: $state.snapshot_id,
    generated_at: $state.observed_at,
    status: "foundation_slice_ready_for_review",
    boundary: {
      external_writes_allowed: $state.external_writes_allowed,
      authorized_task_ids: [$state.tasks[] | select(.status == "approved") | .task_id],
      explicitly_excluded: [
        "connector reauthentication or scope expansion",
        "production or customer-data writes",
        "deployments and scenario runs",
        "publication, contact enrichment, and outreach",
        "billing changes",
        "repository archival, transfer, or deletion"
      ]
    },
    coverage: {
      public_repositories: $repos.counts.total,
      company_repository_coverage_complete: false,
      source_status_counts: ($state.sources | count_by("status")),
      connection_status_counts: ($state.connections | count_by("status")),
      supabase_projects_observed: ([$state.projects[] | select(.provider == "Supabase")] | length),
      supabase_projects_mapped: ([$state.projects[] | select(.provider == "Supabase" and .mapping_status == "mapped")] | length),
      open_conflicts: ($open_conflicts | length),
      baseline_artifacts: ($state.baseline_artifacts | length)
    },
    controls: {
      schemas: 11,
      deterministic_validator: "foundation/validate.jq",
      edge_fixture: "foundation/fixtures/edge-cases.json",
      accepted_memories_indexed: ([$state.memory_candidates[] | select(.status == "accepted" and .indexed)] | length),
      nonaccepted_memories_indexed: ([$state.memory_candidates[] | select(.status != "accepted" and .indexed)] | length),
      current_write_approval_count: ([$state.approvals[] | select(.status == "approved" and .approval_class != "implementation")] | length)
    },
    financial: {
      monthly_software_cost_usd: $cost.monthly_software_cost_usd,
      annual_software_cost_usd: $cost.annual_software_cost_usd,
      minimum_collected_revenue_goal_usd: $repos.targets.minimum_collected_revenue_usd,
      operating_collected_revenue_goal_usd: $repos.targets.operating_revenue_target_usd,
      collected_revenue_usd: $revenue_state.collected_revenue_usd,
      fixture_evidenced_revenue_usd: ($state.revenue_events | evidenced_revenue),
      external_launch_status: $launch_state.overall_status
    },
    blockers: (
      ([$incomplete_sources[] | {
        type: "source",
        id: .source_id,
        status: .status,
        action: .gap,
        evidence_ref: .evidence_ref
      }])
      + ([$unmapped_projects[] | {
        type: "project_mapping",
        id: .project_id,
        status: .mapping_status,
        action: "Assign canonical repository, deployment, data owner/classification, backup evidence, and cost.",
        evidence_ref: .evidence_refs[0]
      }])
      + ([$open_conflicts[] | {
        type: "conflict",
        id: .conflict_id,
        status: .status,
        action: .resolution_required,
        evidence_ref: .evidence_refs[0]
      }])
    ),
    access_requests: [
      $pending_approvals[]
      | select(.approval_class == "access")
      | {
          approval_id,
          action,
          requested_from,
          evidence_refs
        }
    ],
    human_approvals: [
      $pending_approvals[]
      | {
          approval_id,
          approval_class,
          action,
          status,
          requested_from
        }
    ],
    next_slice: [
      "Review this foundation diff and keep G1 through G7 closed until their evidence packets are ready.",
      "Request least-privilege GitHub repository/settings read scope and reconcile public, private, organization, archived, and transferred totals.",
      "Collect a fresh account-scoped Make organization, team, scenario, execution-history, credit, reset, and rollover snapshot to resolve the open conflict.",
      "Map all four Supabase projects to source, deployment, owner, data class, backup, and cost without reading application rows.",
      "Persist and freshness-check the 25 organization-level staffing prospects with outreach_authorized=false.",
      "Prepare G2 evidence before provisioning a Supabase branch or gateway credentials for the engineering-memory pilot."
    ]
  }
