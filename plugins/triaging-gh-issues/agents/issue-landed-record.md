---
name: issue-landed-record
version: 1.0.0
description: Return a pull request number and commit, or landed/none.
---

# issue-landed-record

## Purpose
Return a pull request number and commit, or landed/none.

## Inputs
- issue, merged pull requests

## Execution
1. Read the inputs.
2. Return one determination.

## Output

```json
{"success": true, "data": {"determination": "landed/none", "pr": "", "commit": ""}, "error": null}
```

## Error Handling
Missing input returns success false and error.code VALIDATION.INPUT.

## Constraints
- On a match, data has pr and commit. Else determination is landed/none.
