---
name: pr-author-credit
version: 1.0.0
description: Return the credit line for a replacement pull request.
---

# pr-author-credit

## Purpose
Return the credit line for a replacement pull request.

## Inputs
- prpair label, original author

## Execution
1. Read the inputs.
2. Return one determination.

## Output

```json
{"success": true, "data": {"determination": "Credits: @login in #1", "coauthor": "Co-authored-by: Name <email>"}, "error": null}
```

## Error Handling
Missing input returns success false and error.code VALIDATION.INPUT.

## Constraints
- data.determination is the Credits line.
- data.coauthor is the Co-authored-by trailer. Do not close either pull request.
