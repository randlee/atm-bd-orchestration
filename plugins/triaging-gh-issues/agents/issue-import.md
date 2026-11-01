---
name: issue-import
version: 1.0.0
description: Create the incoming bead.
---

# issue-import

## Purpose
Create the incoming bead.

## Inputs
- issue id

## Execution
1. Read the inputs.
2. Return one determination.

## Output

```json
{"success": true, "data": {"determination": "bead id"}, "error": null}
```

## Error Handling
Missing input returns success false and error.code VALIDATION.INPUT.

## Constraints
- Set status/needs-triage. Copy GitHub labels onto the bead.
