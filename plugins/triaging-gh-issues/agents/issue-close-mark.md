---
name: issue-close-mark
version: 1.0.0
description: Return status/close.
---

# issue-close-mark

## Purpose
Return status/close.

## Inputs
- comments

## Execution
1. Read the inputs.
2. Return one determination.

## Output

```json
{"success": true, "data": {"determination": "status/close"}, "error": null}
```

## Error Handling
Missing input returns success false and error.code VALIDATION.INPUT.

## Constraints
- Return status/close only when LANDED and QA-APPROVED items=all are present.
- Do not close the issue.
