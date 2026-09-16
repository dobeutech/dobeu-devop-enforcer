#!/usr/bin/env bash
set -euo pipefail

foundation_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
workspace_dir=$(cd "$foundation_dir/.." && pwd)
mode=${1:-write}
temp_dir=$(mktemp -d)
json_temp="$temp_dir/readiness.json"
markdown_temp="$temp_dir/readiness.md"

cleanup() {
  rm -f "$json_temp" "$markdown_temp"
  rmdir "$temp_dir"
}
trap cleanup EXIT

if [[ "$mode" != "write" && "$mode" != "--check" ]]; then
  printf 'Usage: %s [--check]\n' "$0" >&2
  exit 2
fi

"$foundation_dir/validate.sh" >/dev/null

jq \
  --slurpfile repositories "$workspace_dir/portfolio/repositories.json" \
  --slurpfile costs "$workspace_dir/portfolio/cost-map.json" \
  --slurpfile launch "$workspace_dir/portfolio/launch-readiness.json" \
  --slurpfile revenue "$workspace_dir/portfolio/revenue-control.json" \
  -f "$foundation_dir/reports/readiness.jq" \
  "$foundation_dir/state.json" > "$json_temp"

jq -r -f "$foundation_dir/reports/readiness-md.jq" "$json_temp" > "$markdown_temp"

if [[ "$mode" == "--check" ]]; then
  [[ -f "$foundation_dir/readiness.json" && -f "$foundation_dir/readiness.md" ]] || {
    printf 'Readiness outputs are missing; run ./foundation/report.sh\n' >&2
    exit 1
  }
  cmp -s "$json_temp" "$foundation_dir/readiness.json" || {
    printf 'foundation/readiness.json is stale; run ./foundation/report.sh\n' >&2
    exit 1
  }
  cmp -s "$markdown_temp" "$foundation_dir/readiness.md" || {
    printf 'foundation/readiness.md is stale; run ./foundation/report.sh\n' >&2
    exit 1
  }
  printf 'Readiness report is current for snapshot %s\n' "$(jq -r '.generated_from_snapshot' "$json_temp")"
else
  mv "$json_temp" "$foundation_dir/readiness.json"
  mv "$markdown_temp" "$foundation_dir/readiness.md"
  printf 'Generated foundation/readiness.json and foundation/readiness.md\n'
fi
