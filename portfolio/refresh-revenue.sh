#!/usr/bin/env bash
set -euo pipefail

portfolio_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
as_of=$(date -u +%Y-%m-%dT%H:%M:%SZ)
json_tmp=$(mktemp)
md_tmp=$(mktemp)
trap 'rm -f "$json_tmp" "$md_tmp"' EXIT

jq \
  --slurpfile portfolio "$portfolio_dir/repositories.json" \
  --slurpfile costs "$portfolio_dir/cost-map.json" \
  --arg as_of "$as_of" \
  -f "$portfolio_dir/revenue-report.jq" \
  "$portfolio_dir/revenue-ledger.json" > "$json_tmp"

jq -r -f "$portfolio_dir/revenue-report-md.jq" "$json_tmp" > "$md_tmp"

mv "$json_tmp" "$portfolio_dir/revenue-control.json"
mv "$md_tmp" "$portfolio_dir/revenue-dashboard.md"

printf 'Revenue dashboard refreshed: $%s collected, $%s remaining to exceed baseline software cost\n' \
  "$(jq -r '.collected_revenue_usd' "$portfolio_dir/revenue-control.json")" \
  "$(jq -r '.gap_to_exceed_cost_usd' "$portfolio_dir/revenue-control.json")"
