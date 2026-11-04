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
