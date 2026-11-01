---
name: issue-security-classify
version: 1.0.0
description: Return one security label.
---

# issue-security-classify

## Purpose
Return one security label.

## Inputs
- title, body

## Execution
1. Read the inputs.
2. Return one determination.

## Output

```json
{"success": true, "data": {"determination": "security/none"}, "error": null}
```

## Error Handling
Missing input returns success false and error.code VALIDATION.INPUT.

## Constraints
- One of security/none, security/review.
