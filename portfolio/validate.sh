#!/usr/bin/env bash
set -euo pipefail

portfolio_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
data="$portfolio_dir/repositories.json"
costs="$portfolio_dir/cost-map.json"
connectors="$portfolio_dir/connector-status.json"
source_data="$portfolio_dir/repositories-source.json"
config="$portfolio_dir/config.json"
schema_validator="$portfolio_dir/../foundation/validate-schema.py"
temp_dir=$(mktemp -d)
expected_portfolio="$temp_dir/repositories.json"
expected_ranking="$temp_dir/revenue-ranking.md"
expected_revenue="$temp_dir/revenue-control.json"
expected_dashboard="$temp_dir/revenue-dashboard.md"
affiliated_revenue="$temp_dir/affiliated-revenue.json"
unaffiliated_revenue="$temp_dir/unaffiliated-revenue.json"

cleanup() {
  rm -f \
    "$expected_portfolio" \
    "$expected_ranking" \
    "$expected_revenue" \
    "$expected_dashboard" \
    "$affiliated_revenue" \
    "$unaffiliated_revenue"
  rmdir "$temp_dir"
}
trap cleanup EXIT

for command_name in cmp jq mktemp python3; do
  command -v "$command_name" >/dev/null 2>&1 || {
    printf 'Portfolio validation failed: missing required command: %s\n' "$command_name" >&2
    exit 1
  }
done

jq -e --slurpfile source "$source_data" '
  .schema == "revenue-portfolio/v1"
  and .counts.total == ($source[0] | length)
  and (.repositories | length) == .counts.total
  and ([.repositories[].name] | unique | length) == .counts.total
  and ([.repositories[].name] | sort) == ([$source[0][].name] | sort)
  and ([.repositories[].score | select(. < 0 or . > 100)] | length) == 0
  and ([.repositories[].rank] == [range(1; .counts.total + 1)])
  and (.targets.annual_software_cost_usd == 7776)
  and (.targets.minimum_collected_revenue_usd > .targets.annual_software_cost_usd)
  and (.targets.operating_revenue_target_usd >= .targets.minimum_collected_revenue_usd)
  and .source.coverage != ""
  and ([.repositories[] | select(.monthly_direct_cost_usd == null)] | length) > 0
' "$data" >/dev/null

jq -e '
  ."$schema" == "cost-portfolio/v1"
  and .monthly_software_cost_usd == 648
  and .annual_software_cost_usd == 7776
  and .monthly_software_cost_usd == ([.subscriptions[].monthly_cost_usd] | add)
  and .annual_software_cost_usd == (.monthly_software_cost_usd * 12)
  and (.subscriptions | length) == 15
  and .prepaid_capacity[0].remaining_observed == 133003.65
  and ([.subscriptions[].id] | unique | length) == (.subscriptions | length)
  and ([.subscriptions[] | select(.monthly_cost_usd <= 0)] | length) == 0
  and ([.subscriptions[] | select((.recommended_action | length) == 0)] | length) == 0
  and .scenario_bookends.protected_technical_foundation_monthly_usd == 74
' "$costs" >/dev/null

jq -e '
  ."$schema" == "connector-evidence/v1"
  and ([.connectors[].name] | sort) == ["Composio", "GitHub", "Make", "Supabase"]
  and (.connectors | map(select(.name == "Supabase"))[0].projects | length) == 4
  and (.connectors | map(select(.name == "Supabase"))[0].projects | map(select(.name == "RouteReady" and .mapping_status == "unmapped")) | length) == 1
  and (.connectors | map(select(.name == "Make"))[0].native_status == "not_ready_no_setup_path")
' "$connectors" >/dev/null

jq -e '
  ."$schema" == "revenue-launch-readiness/v1"
  and .offer_id == "staffing_workflow_diagnostic"
  and .overall_status == "internal_pack_complete_external_launch_awaiting_approval"
  and (.gates | map(select(.id == "source-readiness" and .status == "failed_for_product_launch")) | length) == 1
  and (.gates | map(select(.id == "payment" and .status == "manual_or_hosted_only")) | length) == 1
  and (.gates | map(select(.id == "revenue-proof" and .status == "not_met")) | length) == 1
  and (.minimum_human_decisions | length) == 4
' "$portfolio_dir/launch-readiness.json" >/dev/null

jq -e --slurpfile costs "$costs" '
  .targets.annual_software_cost_usd == $costs[0].annual_software_cost_usd
' "$data" >/dev/null

jq -e '
  (.repositories | map(select(.name == "unique-staffing-prof" and .decision == "invest_and_sell_now")) | length) == 1
  and (.repositories | map(select(.name == "dobeucloud" and .decision == "package_and_validate")) | length) == 1
  and (.repositories | map(select(.name == "security-agent" and .decision == "remove_from_active_portfolio")) | length) == 1
  and (.gaps | map(.id) | index("routeready-source") != null)
' "$data" >/dev/null

grep -q '^# Revenue Portfolio Ranking$' "$portfolio_dir/revenue-ranking.md"
grep -q "Public repositories ranked: $(jq -r '.counts.total' "$data")" "$portfolio_dir/revenue-ranking.md"
grep -q '^# Cost and Tool Consolidation Actions$' "$portfolio_dir/cost-actions.md"
grep -q '^# Make Credit Sprint$' "$portfolio_dir/make-credit-sprint.md"
test "$(wc -l < "$portfolio_dir/revenue-ledger.csv")" -eq 1
test -s "$portfolio_dir/templates/diagnostic.md"
test -s "$portfolio_dir/templates/sow.md"
test -s "$portfolio_dir/templates/outcome-report.md"
test -s "$portfolio_dir/templates/repository-retirement.md"

jq -e '
  ."$schema" == "revenue-ledger/v1"
  and .currency == "USD"
  and .period_start < .period_end
  and ([.opportunities[].opportunity_id] | unique | length) == (.opportunities | length)
  and ([.opportunities[].payments[].payment_id] | unique | length) == ([.opportunities[].payments[]] | length)
' "$portfolio_dir/revenue-ledger.json" >/dev/null

python3 "$schema_validator" \
  "$portfolio_dir/revenue-ledger.schema.json" \
  "$portfolio_dir/revenue-ledger.json" >/dev/null

jq -e --slurpfile ledger "$portfolio_dir/revenue-ledger.json" '
  .schema == "revenue-control/v1"
  and .baseline_software_cost_usd == 7776
  and .minimum_collected_revenue_goal_usd == 7777
  and .collected_revenue_usd >= 0
  and (.revenue_exceeds_baseline_software_cost == (.collected_revenue_usd > .baseline_software_cost_usd))
  and (.evidence.opportunity_count == ($ledger[0].opportunities | length))
  and (.evidence.duplicate_opportunity_ids | length) == 0
  and (.evidence.duplicate_payment_ids | length) == 0
' "$portfolio_dir/revenue-control.json" >/dev/null

grep -q '^# Revenue Control Dashboard$' "$portfolio_dir/revenue-dashboard.md"

snapshot=$(jq -r '.generated_at' "$data")
jq --arg snapshot "$snapshot" \
  --slurpfile config "$config" \
  -f "$portfolio_dir/score.jq" \
  "$source_data" > "$expected_portfolio"
cmp -s "$expected_portfolio" "$data" || {
  printf 'portfolio/repositories.json is stale; run ./portfolio/refresh.sh\n' >&2
  exit 1
}

jq -r -f "$portfolio_dir/report.jq" "$expected_portfolio" > "$expected_ranking"
cmp -s "$expected_ranking" "$portfolio_dir/revenue-ranking.md" || {
  printf 'portfolio/revenue-ranking.md is stale; run ./portfolio/refresh.sh\n' >&2
  exit 1
}

revenue_generated_at=$(jq -r '.generated_at' "$portfolio_dir/revenue-control.json")
jq \
  --slurpfile portfolio "$data" \
  --slurpfile costs "$costs" \
  --arg as_of "$revenue_generated_at" \
  -f "$portfolio_dir/revenue-report.jq" \
  "$portfolio_dir/revenue-ledger.json" > "$expected_revenue"
cmp -s "$expected_revenue" "$portfolio_dir/revenue-control.json" || {
  printf 'portfolio/revenue-control.json is stale; run ./portfolio/refresh-revenue.sh\n' >&2
  exit 1
}

jq -r -f "$portfolio_dir/revenue-report-md.jq" "$expected_revenue" > "$expected_dashboard"
cmp -s "$expected_dashboard" "$portfolio_dir/revenue-dashboard.md" || {
  printf 'portfolio/revenue-dashboard.md is stale; run ./portfolio/refresh-revenue.sh\n' >&2
  exit 1
}

jq '.opportunities = [{
  opportunity_id: "owner-funded-001",
  customer_alias: "workspace-owner",
  offer_id: "other_approved",
  stage: "closed_won",
  proposed_amount_usd: 8000,
  contracted_amount_usd: 8000,
  source_repositories: [],
  payments: [{
    payment_id: "owner-payment-001",
    kind: "payment",
    amount_usd: 8000,
    status: "settled",
    collected_at: "2026-09-12T00:00:00Z",
    evidence_reference: "fixture://owner-transfer",
    unaffiliated_customer: false
  }],
  evidence_references: ["fixture://owner-transfer"],
  next_action: "Exclude this affiliated fixture from revenue."
}]' "$portfolio_dir/revenue-ledger.json" \
  | jq \
      --slurpfile portfolio "$data" \
      --slurpfile costs "$costs" \
      --arg as_of "2026-09-12T00:00:00Z" \
      -f "$portfolio_dir/revenue-report.jq" > "$affiliated_revenue"

jq -e '
  .collected_revenue_usd == 0
  and .revenue_exceeds_baseline_software_cost == false
  and .evidence.settled_payment_records_affiliated_or_unknown == 1
' "$affiliated_revenue" >/dev/null

jq '.opportunities = [{
  opportunity_id: "customer-funded-001",
  customer_alias: "unaffiliated-customer",
  offer_id: "other_approved",
  stage: "closed_won",
  proposed_amount_usd: 8000,
  contracted_amount_usd: 8000,
  source_repositories: [],
  payments: [{
    payment_id: "customer-payment-001",
    kind: "payment",
    amount_usd: 8000,
    status: "settled",
    collected_at: "2026-09-12T00:00:00Z",
    evidence_reference: "fixture://customer-receipt",
    unaffiliated_customer: true
  }],
  evidence_references: ["fixture://customer-receipt"],
  next_action: "Verify this unaffiliated fixture counts as revenue."
}]' "$portfolio_dir/revenue-ledger.json" \
  | jq \
      --slurpfile portfolio "$data" \
      --slurpfile costs "$costs" \
      --arg as_of "2026-09-12T00:00:00Z" \
      -f "$portfolio_dir/revenue-report.jq" > "$unaffiliated_revenue"

jq -e '
  .collected_revenue_usd == 8000
  and .revenue_exceeds_baseline_software_cost == true
  and .evidence.settled_payment_records_affiliated_or_unknown == 0
' "$unaffiliated_revenue" >/dev/null

jq -e '
  .intake_id == "synthetic-northstar-001"
  and .disposition == "invite_to_scope_call"
  and .modeled_operator_hours_per_month == 23.09
  and (.required_gates | index("security_and_data_review") != null)
' <(jq -f "$portfolio_dir/offer/qualification.jq" "$portfolio_dir/offer/synthetic-intake.json") >/dev/null

printf 'Portfolio validation passed for %s repositories\n' "$(jq -r '.counts.total' "$data")"
