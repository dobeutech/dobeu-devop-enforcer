#!/usr/bin/env bash
set -euo pipefail

portfolio_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
owner=$(jq -r '.owner' "$portfolio_dir/config.json")
snapshot=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
temp_dir=$(mktemp -d)
source_tmp="$temp_dir/repositories-source.json"
page_tmp="$temp_dir/page.json"
merged_tmp="$temp_dir/merged.json"
ranked_tmp="$temp_dir/repositories.json"
report_tmp="$temp_dir/revenue-ranking.md"

cleanup() {
  rm -f "$source_tmp" "$page_tmp" "$merged_tmp" "$ranked_tmp" "$report_tmp"
  rmdir "$temp_dir"
}
trap cleanup EXIT

curl_args=(
  --fail
  --silent
  --show-error
  --location
  --retry 3
  --header 'Accept: application/vnd.github+json'
  --header 'X-GitHub-Api-Version: 2022-11-28'
)

if [[ -n "${GITHUB_TOKEN:-}" ]]; then
  curl_args+=(--header "Authorization: Bearer ${GITHUB_TOKEN}")
fi

jq -n '[]' > "$source_tmp"
page=1
max_pages=100

while (( page <= max_pages )); do
  curl "${curl_args[@]}" \
    "https://api.github.com/users/${owner}/repos?per_page=100&type=owner&sort=updated&page=${page}" \
    --output "$page_tmp"

  jq -e 'type == "array"' "$page_tmp" >/dev/null
  page_count=$(jq -r 'length' "$page_tmp")
  jq -s '.[0] + .[1]' "$source_tmp" "$page_tmp" > "$merged_tmp"
  mv "$merged_tmp" "$source_tmp"

  if (( page_count < 100 )); then
    break
  fi
  page=$((page + 1))
done

if (( page > max_pages )); then
  printf 'Repository refresh exceeded the %s-page safety limit\n' "$max_pages" >&2
  exit 1
fi

jq --arg snapshot "$snapshot" \
  --slurpfile config "$portfolio_dir/config.json" \
  -f "$portfolio_dir/score.jq" \
  "$source_tmp" > "$ranked_tmp"

jq -r -f "$portfolio_dir/report.jq" "$ranked_tmp" > "$report_tmp"

mv "$ranked_tmp" "$portfolio_dir/repositories.json"
mv "$report_tmp" "$portfolio_dir/revenue-ranking.md"
mv "$source_tmp" "$portfolio_dir/repositories-source.json"

printf 'Generated %s public repository records at %s\n' \
  "$(jq -r '.counts.total' "$portfolio_dir/repositories.json")" \
  "$snapshot"
