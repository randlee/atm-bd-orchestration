---
name: issue-release-close
version: 1.0.0
description: Return closed or the missing check.
---

# issue-release-close

## Purpose
Return closed or the missing check.

## Inputs
- release label, comments

## Execution
1. Read the inputs.
2. Return one determination.

## Output

```json
{"success": true, "data": {"determination": "closed"}, "error": null}
```

## Error Handling
Missing input returns success false and error.code VALIDATION.INPUT.

## Constraints
- Close only when the release is published and both evidence lines match.
- Do not add status/close.
