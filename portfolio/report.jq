def cell:
  if . == null then "—" else tostring | gsub("[|\\r\\n]"; " ") end;

. as $doc
| ($doc.repositories | to_entries | map(
    "| \(.value.rank) | [\(.value.name)](\(.value.url)) | \(.value.score) | \(.value.decision | cell) | \(.value.portfolio_role | cell) | \(.value.cost_pressure | cell) | \(.value.confidence | cell) |"
  )) as $rows
| ($doc.repositories | group_by(.decision) | map({decision: .[0].decision, count: length}) | sort_by(-.count)) as $groups
| [
    "# Revenue Portfolio Ranking",
    "",
    "Generated: \($doc.generated_at)",
    "",
    "> Coverage: \($doc.source.coverage). This is an evidence-backed prioritization, not proof of product-market fit or authorization to delete a repository.",
    "",
    "## Executive decision",
    "",
    "Sell a **Staffing Operations Automation Diagnostic** before building another SaaS product. Use `unique-staffing-prof` only as rights-safe domain proof after its build and test gates pass. Treat `dobeucloud` as a sales/delivery foundation under repair; use an approved provider-hosted or manual invoice instead of its current custom checkout. Use `dobeu-devop-enforcer` as the second service line only after its permission and evidence gates pass.",
    "",
    "The annual software ceiling is **$\($doc.targets.annual_software_cost_usd)**. The literal collected-revenue floor is **$\($doc.targets.minimum_collected_revenue_usd)** and the operating target is **$\($doc.targets.operating_revenue_target_usd)**. Repository activity or generated assets do not count as revenue.",
    "",
    "## Coverage and decision totals",
    "",
    "- Public repositories ranked: \($doc.counts.total)",
    "- Active first-party repositories: \($doc.counts.active_owned)",
    "- Active placeholders: \($doc.counts.placeholders)",
    "- Active forks: \($doc.counts.active_forks)",
    "- Archived first-party repositories: \($doc.counts.archived_owned)",
    "- Archived forks: \($doc.counts.archived_forks)",
    "",
    ($groups[] | "- `\(.decision)`: \(.count)"),
    "",
    "## Ranked portfolio",
    "",
    "| Rank | Repository | Score | Decision | Role | Cost pressure | Confidence |",
    "|---:|---|---:|---|---|---|---|",
    $rows[],
    "",
    "Scores compare near-term customer value, time to revenue, differentiation, execution readiness, strategic leverage, and maintenance penalty. They do **not** assign shared subscription cost to a repository without invoice/runtime evidence.",
    "",
    "## Expert action bands",
    "",
    "### Invest and sell now",
    "",
    ($doc.repositories[] | select(.decision == "invest_and_sell_now") | "- **\(.name):** \(.why) Next: \(.next_action)"),
    "",
    "### Package and validate",
    "",
    ($doc.repositories[] | select(.decision == "package_and_validate") | "- **\(.name):** \(.why) Next: \(.next_action)"),
    "",
    "### Consolidate, retain internally, or remove from active work",
    "",
    ($doc.repositories[] | select(.decision != "invest_and_sell_now" and .decision != "package_and_validate") | "- **\(.name)** (`\(.decision)`): \(.next_action)"),
    "",
    "## Evidence gaps that block irreversible decisions",
    "",
    ($doc.gaps[] | "- **\(.id):** \(.impact)"),
    "",
    "No repository should be deleted from this ranking alone. Archive/delete packets require consumer, deployment, domain, package, retention, license, backup, and owner evidence."
  ]
| .[]
