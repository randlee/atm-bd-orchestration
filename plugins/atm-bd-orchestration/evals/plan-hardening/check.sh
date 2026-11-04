#!/bin/sh
# Read-only validation of one un-squashed evaluation run.
set -eu
if [ "$#" -ne 2 ]; then
    printf '%s\n' 'usage: check.sh <root> <teammate|subagent>' >&2
    exit 2
fi
root=$1
runner=$2
case $runner in teammate|subagent) ;; *) printf 'invalid runner: %s\n' "$runner" >&2; exit 2 ;; esac
BD=${BD:-bd}
ATM=${ATM:-atm}
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
planted=$script_dir/planted.json
fixes=$("$BD" list --parent "$root" -l stage:plan-fix --all -n 0 --json)
printf '%s\n' "$fixes" | jq -e 'type == "array"' >/dev/null
if ! printf '%s\n' "$fixes" | jq -r '.[].id' | { failed=0; while IFS= read -r id; do
    fix=$("$BD" show "$id" --json)
    if ! printf '%s\n' "$fix" | jq -e 'length == 1 and .[0].status == "closed" and ((.[0].notes // "") | test("fixed:|rebutted:"; "i"))' >/dev/null; then
        printf 'finding %s was not fixed or rebutted and verified closed\n' "$id" >&2
        failed=1
    fi
done; exit "$failed"; }; then
    exit 1
fi
planted_ids=$(jq -er 'if type == "object" and length > 0 and all(.[]; type == "string" and length > 0) then .[] else error("invalid planted map") end' "$planted")
printf '%s\n' "$planted_ids" | while IFS= read -r bead; do
    if ! printf '%s\n' "$fixes" | jq -e --arg bead "$bead" 'any(.[]; .metadata.plan_bead == $bead)' >/dev/null; then
        printf 'missing plan-fix bead for %s\n' "$bead" >&2
        exit 1
    fi
done
steps=$("$BD" list -l phase-z,stage:plan-hardening --include-ephemeral --all -n 0 --json)
# Labels use phase-z; metadata ties each wisp step to this exact fixture root.
steps=$(printf '%s\n' "$steps" | jq -ce --arg root "$root" '[.[] | select(.metadata.root == $root)]')
for item in '1:scope' '1:critical' '1:fix' 'final:ceremony' 'final:fix' 'final:verify'; do
    iteration=${item%:*}
    pass=${item#*:}
    if ! printf '%s\n' "$steps" | jq -e --arg i "$iteration" --arg p "$pass" \
        'any(.[]; (.metadata.iteration | tostring) == $i and .metadata.pass == $p)' >/dev/null; then
        printf 'missing step %s\n' "$item" >&2
        exit 1
    fi
done
printf '%s\n' "$steps" | jq -er '.[].id' | while IFS= read -r step; do
    row=$("$BD" show "$step" --json)
    if ! printf '%s\n' "$row" | jq -e 'length == 1 and .[0].status == "closed" and (.[0].close_reason | type == "string" and test("(^|[[:space:]])VERDICT=(PASS|FAIL)([[:space:]]|$)"))' >/dev/null; then
        printf 'step %s lacks a closed PASS/FAIL verdict\n' "$step" >&2
        exit 1
    fi
    step_pass=$(printf '%s\n' "$steps" | jq -er --arg step "$step" '.[] | select(.id == $step) | .metadata.pass')
    if [ "$step_pass" = fix ] || [ "$step_pass" = verify ]; then
        if ! printf '%s\n' "$row" | jq -e '.[0].close_reason | test("(^|[[:space:]])VERDICT=PASS([[:space:]]|$)")' >/dev/null; then
            printf 'step %s did not pass\n' "$step" >&2
            exit 1
        fi
    fi
    reason=$(printf '%s\n' "$row" | jq -er '.[0].close_reason')
    detected=$(printf '%s\n' "$reason" | sed -nE 's/.*(^|[[:space:]])detected=([0-9]+)([[:space:]]|$).*/\2/p')
    filed=$(printf '%s\n' "$reason" | sed -nE 's/.*(^|[[:space:]])filed=([^[:space:]]+).*/\2/p')
    if [ -z "$detected" ] || [ -z "$filed" ]; then
        printf 'step %s lacks detected/ filed accounting\n' "$step" >&2
        exit 1
    fi
    if [ "$filed" = none ]; then count=0; else count=$(printf '%s\n' "$filed" | tr ',' '\n' | wc -l | tr -d ' '); fi
    if [ "$detected" -ne "$count" ]; then
        printf 'step %s detected %s findings but filed %s\n' "$step" "$detected" "$count" >&2
        exit 1
    fi
    if [ "$filed" != none ]; then
        for id in $(printf '%s\n' "$filed" | tr ',' ' '); do
            if ! printf '%s\n' "$fixes" | jq -e --arg id "$id" --arg step "$step" 'any(.[]; .id == $id and .metadata.filed_by_step == $step)' >/dev/null; then
                printf 'step %s filed missing or misattributed finding %s\n' "$step" "$id" >&2
                exit 1
            fi
        done
    fi
    events=$("$ATM" task events "$step" --json)
    if [ "$runner" = teammate ]; then
        if ! printf '%s\n' "$events" | jq -e '[.events[].event] as $e | ($e | index("started")) as $a | ($e | index("completed")) as $b | $a != null and $b != null and $a < $b' >/dev/null; then
            printf 'step %s lacks ordered ATM start and close\n' "$step" >&2
            exit 1
        fi
    else
        if ! printf '%s\n' "$events" | jq -e '(.events | type == "array" and length == 0)' >/dev/null; then
            printf 'subagent step %s has an ATM task\n' "$step" >&2
            exit 1
        fi
    fi
done
printf 'PASS: %s (%s): all planted beads and step lifecycle checks passed\n' "$root" "$runner"
