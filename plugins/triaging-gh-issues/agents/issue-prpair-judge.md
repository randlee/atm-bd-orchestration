---
name: issue-prpair-judge
version: 1.0.0
description: Return prpair/none or prpair/#N.
---

# issue-prpair-judge

## Purpose
Return prpair/none or prpair/#N.

## Inputs
- title, open pull request numbers

## Execution
1. Read the inputs.
2. Return one determination.

## Output

```json
{"success": true, "data": {"determination": "prpair/none"}, "error": null}
```

## Error Handling
Missing input returns success false and error.code VALIDATION.INPUT.

## Constraints
- One label. Leave both pull requests open.
