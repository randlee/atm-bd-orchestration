---
name: issue-area-classify
version: 1.0.0
description: Return one area label.
---

# issue-area-classify

## Purpose
Return one area label.

## Inputs
- title, body

## Execution
1. Read the inputs.
2. Return one determination.

## Output

```json
{"success": true, "data": {"determination": "area/product"}, "error": null}
```

## Error Handling
Missing input returns success false and error.code VALIDATION.INPUT.

## Constraints
- One of area/product, area/skills, area/workflows.
