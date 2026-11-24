#!/usr/bin/env bash
# Apply or verify the GitHub repository settings stored as code.
#
#   .github/settings/repository.json   merge strategy, Actions hardening, security features
#   .github/rulesets/protect-main.json branch ruleset for main
#
# Usage:
#   scripts/repo-settings.sh apply       apply every setting to GitHub (admin only)
#   scripts/repo-settings.sh verify      compare GitHub with the files, exit 1 on drift
#   scripts/repo-settings.sh test-push   prove that a direct push to main is rejected
#
# Requirements: gh (authenticated as a repository admin) and jq.

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

SETTINGS=".github/settings/repository.json"
RULESET=".github/rulesets/protect-main.json"
failures=0

init() {
  REPO="${REPO:-$(gh repo view --json nameWithOwner --jq .nameWithOwner)}"
  RULESET_NAME="$(jq -r .name "$RULESET")"
  API="repos/$REPO"
}

pass() { printf '  \033[32m✔\033[0m %s\n' "$1"; }
fail() { printf '  \033[31m✘\033[0m %s\n' "$1"; failures=$((failures + 1)); }
section() { printf '\n\033[1m%s\033[0m\n' "$1"; }
setting() { jq -c "$1" "$SETTINGS"; }

# Succeeds when the JSON document $1 contains every key and value of the JSON document $2.
contains() { jq -e --argjson expected "$2" 'contains($expected)' <<<"$1" >/dev/null; }

ruleset_id() {
  gh api "$API/rulesets" --jq ".[] | select(.name == \"$RULESET_NAME\") | .id"
}

toggle() {
  # toggle <endpoint> <true|false>: enable with PUT, disable with DELETE.
  if [[ "$2" == "true" ]]; then
    gh api -X PUT "$API/$1" --silent
  else
    gh api -X DELETE "$API/$1" --silent
  fi
}

apply() {
  section "Repository: merge strategy and secret scanning"
  setting .repository | gh api -X PATCH "$API" --input - --silent
  pass "updated"

  section "GitHub Actions"
  setting '.actions | {default_workflow_permissions, can_approve_pull_request_reviews}' \
    | gh api -X PUT "$API/actions/permissions/workflow" --input - --silent
  setting '.actions | {approval_policy: .fork_pr_approval_policy}' \
    | gh api -X PUT "$API/actions/permissions/fork-pr-contributor-approval" --input - --silent
  pass "updated"

  section "Security features"
  toggle vulnerability-alerts "$(jq -r .security.vulnerability_alerts "$SETTINGS")"
  toggle automated-security-fixes "$(jq -r .security.automated_security_fixes "$SETTINGS")"
  toggle private-vulnerability-reporting "$(jq -r .security.private_vulnerability_reporting "$SETTINGS")"
  if [[ "$(jq -r .security.code_scanning_default_setup "$SETTINGS")" == "true" ]]; then
    gh api -X PATCH "$API/code-scanning/default-setup" -f state=configured --silent
  else
    gh api -X PATCH "$API/code-scanning/default-setup" -f state=not-configured --silent
  fi
  pass "updated"

  section "Ruleset: $RULESET_NAME"
  local id
  id="$(ruleset_id)"
  if [[ -n "$id" ]]; then
    gh api -X PUT "$API/rulesets/$id" --input "$RULESET" --silent
    pass "updated (id $id)"
  else
    gh api -X POST "$API/rulesets" --input "$RULESET" --silent
    pass "created"
  fi

  printf '\nDone. Run "%s verify" to confirm.\n' "$0"
}

verify() {
  section "Repository: merge strategy and secret scanning"
  local repo key expected
  repo="$(gh api "$API")"
  for key in $(jq -r '.repository | keys[]' "$SETTINGS"); do
    expected="$(setting ".repository.$key")"
    if contains "$(jq -c ".$key" <<<"$repo")" "$expected"; then
      pass "$key"
    else
      fail "$key: expected $expected, got $(jq -c ".$key" <<<"$repo")"
    fi
  done

  section "GitHub Actions"
  local workflow fork
  workflow="$(gh api "$API/actions/permissions/workflow")"
  for key in default_workflow_permissions can_approve_pull_request_reviews; do
    expected="$(setting ".actions.$key")"
    if contains "$(jq -c ".$key" <<<"$workflow")" "$expected"; then
      pass "$key"
    else
      fail "$key: expected $expected, got $(jq -c ".$key" <<<"$workflow")"
    fi
  done
  fork="$(gh api "$API/actions/permissions/fork-pr-contributor-approval" --jq .approval_policy)"
  expected="$(jq -r .actions.fork_pr_approval_policy "$SETTINGS")"
  if [[ "$fork" == "$expected" ]]; then
    pass "fork_pr_approval_policy"
  else
    fail "fork_pr_approval_policy: expected $expected, got $fork"
  fi

  section "Security features"
  local alerts fixes reporting codeql
  alerts="$(gh api "$API/vulnerability-alerts" --silent 2>/dev/null && echo true || echo false)"
  fixes="$(gh api "$API/automated-security-fixes" --jq .enabled 2>/dev/null || echo false)"
  reporting="$(gh api "$API/private-vulnerability-reporting" --jq .enabled 2>/dev/null || echo false)"
  codeql="$(gh api "$API/code-scanning/default-setup" --jq '.state == "configured"' 2>/dev/null || echo false)"
  for pair in "vulnerability_alerts:$alerts" "automated_security_fixes:$fixes" \
    "private_vulnerability_reporting:$reporting" "code_scanning_default_setup:$codeql"; do
    key="${pair%%:*}"
    expected="$(jq -r ".security.$key" "$SETTINGS")"
    if [[ "${pair#*:}" == "$expected" ]]; then
      pass "$key"
    else
      fail "$key: expected $expected, got ${pair#*:}"
    fi
  done

  section "Ruleset: $RULESET_NAME"
  local id actual
  id="$(ruleset_id)"
  if [[ -z "$id" ]]; then
    fail "ruleset not found"
  else
    actual="$(gh api "$API/rulesets/$id")"
    for key in enforcement target conditions bypass_actors rules; do
      expected="$(jq -c ".$key" "$RULESET")"
      if contains "$(jq -c ".$key" <<<"$actual")" "$expected"; then
        pass "$key"
      else
        fail "$key differs from $RULESET"
      fi
    done
  fi

  section "Access"
  local collaborators codeowners_errors
  collaborators="$(gh api "$API/collaborators" --jq '[.[].login] | join(", ")')"
  if [[ "$collaborators" == "${REPO%%/*}" ]]; then
    pass "only the owner has access ($collaborators)"
  else
    fail "unexpected collaborators: $collaborators"
  fi
  codeowners_errors="$(gh api "$API/codeowners/errors" --jq '.errors | length')"
  if [[ "$codeowners_errors" == "0" ]]; then
    pass "CODEOWNERS is valid"
  else
    fail "CODEOWNERS has $codeowners_errors error(s)"
  fi

  if ((failures > 0)); then
    printf '\n\033[31m%d check(s) failed.\033[0m Run "%s apply" to fix drift.\n' "$failures" "$0"
    exit 1
  fi
  printf '\n\033[32mAll checks passed.\033[0m\n'
}

test_push() {
  section "Direct push to main"
  git fetch --quiet origin main
  # Build an empty commit on top of origin/main without touching the working tree or branches.
  local before commit output
  before="$(git rev-parse origin/main)"
  commit="$(git commit-tree "origin/main^{tree}" -p origin/main -m "chore: test branch protection")"
  if output="$(git push origin "$commit:refs/heads/main" 2>&1)"; then
    fail "the push was accepted: main is NOT protected"
    printf 'An empty test commit reached main. Remove it with:\n'
    printf '  git push --force origin %s:refs/heads/main\n' "$before"
    exit 1
  fi
  if grep -qi "rule" <<<"$output"; then
    pass "rejected by the ruleset"
    grep -i -m 3 -E "rule|pull request|status check" <<<"$output" | sed 's/^/    /'
  else
    fail "the push failed for another reason:"
    printf '%s\n' "$output"
    exit 1
  fi
}

case "${1:-}" in
  apply) init && apply ;;
  verify) init && verify ;;
  test-push) test_push ;;
  *)
    sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'
    exit 2
    ;;
esac
