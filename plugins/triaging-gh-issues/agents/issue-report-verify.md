---
name: issue-report-verify
version: 1.0.0
description: Return status/verified or status/unverified.
---

# issue-report-verify

## Purpose
Return status/verified or status/unverified.

## Inputs
- title, body, comments

## Execution
1. Read the inputs.
2. Return one determination.

## Output

```json
{"success": true, "data": {"determination": "status/verified"}, "error": null}
```

## Error Handling
Missing input returns success false and error.code VALIDATION.INPUT.

## Constraints
- One label. Check the report is still true.
