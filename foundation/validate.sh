#!/usr/bin/env bash
set -euo pipefail

foundation_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
workspace_dir=$(cd "$foundation_dir/.." && pwd)
state_file="$foundation_dir/state.json"
fixture_file="$foundation_dir/fixtures/edge-cases.json"
validator="$foundation_dir/validate.jq"
schema_validator="$foundation_dir/validate-schema.py"
internal_schema="$foundation_dir/schemas/internal-foundation.schema.json"
readiness_schema="$foundation_dir/schemas/readiness-report.schema.json"

fail() {
  printf 'Foundation validation failed: %s\n' "$1" >&2
  exit 1
}

for command_name in jq sha256sum cmp mktemp python3; do
  command -v "$command_name" >/dev/null 2>&1 || fail "missing required command: $command_name"
done

schema_count=0
for schema_file in "$foundation_dir"/schemas/*.schema.json; do
  jq -e '
    .["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    and (.["$id"] | type == "string" and startswith("https://dobeu.tech/schemas/") and endswith("/v1"))
    and .type == "object"
  ' "$schema_file" >/dev/null || fail "invalid schema metadata: ${schema_file#"$workspace_dir"/}"
  schema_count=$((schema_count + 1))
done

[[ "$schema_count" -eq 11 ]] || fail "expected 11 schemas, found $schema_count"

python3 "$schema_validator" "$internal_schema" "$state_file" "$fixture_file" \
  || fail "foundation state does not satisfy its JSON Schema contracts"

python3 "$schema_validator" \
  "$workspace_dir/portfolio/revenue-ledger.schema.json" \
  "$workspace_dir/portfolio/revenue-ledger.json" \
  || fail "revenue ledger does not satisfy its JSON Schema contract"

jq -e -f "$validator" "$state_file" >/dev/null || fail "current state violates semantic contracts"
jq -e -f "$validator" "$fixture_file" >/dev/null || fail "edge-case fixture violates semantic contracts"

if jq '.tasks[0].external_writes_allowed = true' "$fixture_file" | jq -e -f "$validator" >/dev/null 2>&1; then
  fail "unauthorized external write fixture was accepted"
fi

if jq '.memory_candidates[1].indexed = true' "$fixture_file" | jq -e -f "$validator" >/dev/null 2>&1; then
  fail "indexed rejected-memory fixture was accepted"
fi

if jq '.memory_candidates += [(.memory_candidates[0] | .memory_id = "fixture-memory-duplicate")]' "$fixture_file" | jq -e -f "$validator" >/dev/null 2>&1; then
  fail "duplicate source-revision-locator fixture was accepted"
fi

if jq '
  .observed_at = "not-a-date"
  | .unexpected = true
  | .tasks[0].status = "garbage"
  | .tasks[0].budget.max_tool_calls = -1
  | del(.connections[0].owner)
' "$fixture_file" | python3 "$schema_validator" "$internal_schema" - >/dev/null 2>&1; then
  fail "schema-invalid foundation fixture was accepted"
fi

if jq 'del(.memory_candidates[0].acl_scope)' "$fixture_file" \
  | python3 "$schema_validator" "$internal_schema" - >/dev/null 2>&1; then
  fail "accepted memory without an ACL was accepted"
fi

jq -e '
  ([
    .revenue_events[]
    | select(
        .status == "settled"
        and .collected_at != null
        and (.evidence_ref // "" | length) > 0
        and .unaffiliated_customer == true
      )
    | if .kind == "refund" then -.amount_usd else .amount_usd end
  ] | add // 0) == 750
' "$fixture_file" >/dev/null || fail "unverified or pending fixture revenue was counted"

jq -e '
  any(
    .memory_candidates[];
    .contains_untrusted_instruction == true
    and .status == "rejected"
    and .indexed == false
    and .execution_authorized == false
  )
  and any(.sources[]; .source_system == "github" and .status == "partial" and .coverage.complete == false)
  and any(.conflicts[]; .subject | contains("Make"))
  and any(.projects[]; .provider == "Supabase" and .mapping_status == "unmapped")
' "$fixture_file" >/dev/null || fail "required adversarial and partial fixtures are missing"

while IFS=$'\t' read -r relative_path expected_hash; do
  [[ "$relative_path" != /* && "$relative_path" != *".."* ]] || fail "unsafe baseline path: $relative_path"
  [[ -f "$workspace_dir/$relative_path" ]] || fail "missing baseline artifact: $relative_path"
  actual_hash=$(sha256sum "$workspace_dir/$relative_path" | awk '{print $1}')
  [[ "$actual_hash" == "$expected_hash" ]] || fail "baseline artifact changed: $relative_path"
done < <(jq -r '.baseline_artifacts[] | [.path, .sha256] | @tsv' "$state_file")

"$workspace_dir/portfolio/validate.sh" >/dev/null

if [[ -f "$foundation_dir/readiness.json" ]]; then
  python3 "$schema_validator" "$readiness_schema" "$foundation_dir/readiness.json" \
    || fail "generated readiness report does not satisfy its JSON Schema contract"

  public_repository_count=$(jq -r '.counts.total' "$workspace_dir/portfolio/repositories.json")
  collected_revenue=$(jq -r '.collected_revenue_usd' "$workspace_dir/portfolio/revenue-control.json")
  jq -e \
    --argjson public_repository_count "$public_repository_count" \
    --argjson collected_revenue "$collected_revenue" '
    .schema == "readiness-report/v1"
    and .status == "foundation_slice_ready_for_review"
    and .boundary.external_writes_allowed == false
    and .coverage.public_repositories == $public_repository_count
    and .financial.collected_revenue_usd == $collected_revenue
    and (.blockers | length > 0)
    and ([.human_approvals[].approval_id] | index("G1") != null)
  ' "$foundation_dir/readiness.json" >/dev/null || fail "generated readiness report is invalid"
fi

printf 'Foundation validation passed: %s schemas, %s public repositories, external writes disabled\n' \
  "$schema_count" \
  "$(jq -r '.counts.total' "$workspace_dir/portfolio/repositories.json")"
