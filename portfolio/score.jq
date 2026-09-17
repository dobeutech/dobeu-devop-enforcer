def kind:
  if .archived and .fork then "archived_fork"
  elif .archived then "archived_owned"
  elif .fork then "active_fork"
  elif .size <= 1 then "placeholder"
  else "active_owned"
  end;

def defaults($kind):
  if $kind == "active_owned" then
    {business_value: 4, time_to_revenue: 2, differentiation: 2, execution_readiness: 5, strategic_leverage: 3, maintenance_penalty: 6}
  elif $kind == "placeholder" then
    {business_value: 0, time_to_revenue: 0, differentiation: 0, execution_readiness: 0, strategic_leverage: 1, maintenance_penalty: 6}
  elif $kind == "active_fork" then
    {business_value: 1, time_to_revenue: 0, differentiation: 0, execution_readiness: 4, strategic_leverage: 2, maintenance_penalty: 12}
  elif $kind == "archived_owned" then
    {business_value: 1, time_to_revenue: 0, differentiation: 1, execution_readiness: 1, strategic_leverage: 2, maintenance_penalty: 8}
  else
    {business_value: 0, time_to_revenue: 0, differentiation: 0, execution_readiness: 1, strategic_leverage: 1, maintenance_penalty: 10}
  end;

def clamp_score:
  if . < 0 then 0 elif . > 100 then 100 else . end;

def automatic_decision($score; $kind; $thresholds):
  if $kind == "archived_fork" then "remove_or_reference"
  elif $kind == "archived_owned" then "archive_retention_review"
  elif $kind == "active_fork" then "remove_from_active_portfolio"
  elif $kind == "placeholder" then "archive_candidate"
  elif $score >= $thresholds.invest_and_sell_now then "invest_and_sell_now"
  elif $score >= $thresholds.package_and_validate then "package_and_validate"
  elif $score >= $thresholds.retain_as_enabler then "retain_as_enabler"
  elif $score >= $thresholds.consolidate_or_reference then "consolidate_or_reference"
  else "archive_candidate"
  end;

($config[0]) as $cfg
| . as $source
| [
    $source[]
    | . as $repo
    | ($repo | kind) as $kind
    | ($cfg.overrides[$repo.name] // {}) as $override
    | ((defaults($kind)) * ($override.dimensions // {})) as $dimensions
    | ((
        $dimensions.business_value
        + $dimensions.time_to_revenue
        + $dimensions.differentiation
        + $dimensions.execution_readiness
        + $dimensions.strategic_leverage
        - $dimensions.maintenance_penalty
      ) | clamp_score) as $score
    | {
        name: $repo.name,
        url: $repo.html_url,
        description: $repo.description,
        homepage: $repo.homepage,
        default_branch: $repo.default_branch,
        pushed_at: $repo.pushed_at,
        updated_at: $repo.updated_at,
        archived: $repo.archived,
        fork: $repo.fork,
        size_kb: $repo.size,
        language: $repo.language,
        stars: $repo.stargazers_count,
        open_issues: $repo.open_issues_count,
        portfolio_kind: ($override.portfolio_kind // $kind),
        score: $score,
        dimensions: $dimensions,
        decision: ($override.decision // automatic_decision($score; $kind; $cfg.thresholds)),
        portfolio_role: ($override.portfolio_role // $kind),
        cost_pressure: ($override.cost_pressure // (if $kind == "active_owned" then "unknown" else "low" end)),
        monthly_direct_cost_usd: ($override.monthly_direct_cost_usd // null),
        cost_mapping_status: (if ($override.monthly_direct_cost_usd // null) == null then "unmapped" else "mapped" end),
        confidence: ($override.confidence // (if $kind == "active_owned" then "low" else "high" end)),
        offer: ($override.offer // null),
        why: ($override.why // (if $kind == "archived_fork" then "Archived third-party fork with no observed active consumer or owned revenue path." elif $kind == "archived_owned" then "Archived first-party asset; reuse value and consumers are unverified." elif $kind == "active_fork" then "Active fork with ongoing update/security cost and no observed owned revenue path." elif $kind == "placeholder" then "Empty or near-empty repository with no implementation evidence." else "Active first-party repository without enough product, customer, deployment, or cost evidence for investment." end)),
        next_action: ($override.next_action // (if $kind == "archived_fork" then "Verify provenance/consumer requirement, then delete or retain as a pinned reference through approval." elif $kind == "archived_owned" then "Verify replacement, consumers, legal retention, and reusable assets before deletion." elif $kind == "active_fork" then "Document upstream policy and active consumer, otherwise archive." elif $kind == "placeholder" then "Confirm owner and dependency, then archive rather than leave active." else "Collect customer, traffic, deployment, direct-cost, and ownership evidence before investing." end))
      }
  ]
| sort_by([-.score, .name]) as $ranked
| {
    schema: "revenue-portfolio/v1",
    generated_at: $snapshot,
    source: {
      provider: "GitHub public REST fallback",
      owner: $cfg.owner,
      connector_status: "GitHub MCP authentication succeeded but repository enumeration/content access returned insufficient scope",
      coverage: "public repositories only; private and organization-only repositories unverified"
    },
    targets: {
      annual_software_cost_usd: $cfg.annual_software_cost_usd,
      minimum_collected_revenue_usd: $cfg.minimum_collected_revenue_usd,
      operating_revenue_target_usd: $cfg.operating_revenue_target_usd
    },
    scoring: {
      dimensions: $cfg.score_dimensions,
      thresholds: $cfg.thresholds,
      note: "Scores rank near-term revenue evidence and strategic reuse, not code quality. Direct monthly cost remains null until invoices and runtime telemetry are mapped to repositories."
    },
    counts: {
      total: ($ranked | length),
      active_owned: ([$ranked[] | select(.portfolio_kind == "active_owned")] | length),
      placeholders: ([$ranked[] | select(.portfolio_kind == "placeholder")] | length),
      active_forks: ([$ranked[] | select(.portfolio_kind == "active_fork")] | length),
      archived_owned: ([$ranked[] | select(.portfolio_kind == "archived_owned")] | length),
      archived_forks: ([$ranked[] | select(.portfolio_kind == "archived_fork")] | length)
    },
    gaps: [
      {
        id: "private-and-org-repositories",
        impact: "Cannot assert full-company code coverage until GitHub MCP read scope is repaired."
      },
      {
        id: "routeready-source",
        impact: "RouteReady has an observed Supabase project/cost but no matching public source repository in the 87-repository inventory."
      },
      {
        id: "repo-cost-attribution",
        impact: "The $648 monthly software portfolio is known, but invoices/runtime usage are not yet attributable to individual repositories."
      },
      {
        id: "traction",
        impact: "Traffic, customers, conversion, active users, contracts, and collected revenue are not exposed by repository metadata."
      }
    ],
    repositories: ($ranked | to_entries | map(.value + {rank: (.key + 1)}))
  }
