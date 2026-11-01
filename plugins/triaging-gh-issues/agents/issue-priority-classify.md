---
name: issue-priority-classify
version: 1.0.0
description: Return one priority from p1 to p4.
---

# issue-priority-classify

## Purpose
Return one priority from p1 to p4.

## Inputs
- title, body, contributor

## Execution
1. Read the inputs.
2. Return one determination.

## Output

```json
{"success": true, "data": {"determination": "priority/p1"}, "error": null}
```

## Error Handling
Missing input returns success false and error.code VALIDATION.INPUT.

## Constraints
- If contributor is set and the issue says p1, return priority/p1.
- Never return p0.
