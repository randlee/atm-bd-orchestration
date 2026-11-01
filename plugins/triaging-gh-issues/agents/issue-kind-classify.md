---
name: issue-kind-classify
version: 1.0.0
description: Return one kind label.
---

# issue-kind-classify

## Purpose
Return one kind label.

## Inputs
- title, body

## Execution
1. Read the inputs.
2. Return one determination.

## Output

```json
{"success": true, "data": {"determination": "kind/bug"}, "error": null}
```

## Error Handling
Missing input returns success false and error.code VALIDATION.INPUT.

## Constraints
- One of kind/bug, kind/feature, kind/docs, kind/question.
