# jev-check

The small Jev client used by `atm-bd-lite-gate.py`. It provides the HTTP
transport, `check(state, questions)`, typed Jev errors, question-set loading,
and the gate's Jev input record.

## Request behavior

One `check` sends one JSON request containing `model`, `state`, and `questions`.
Requests over `max_request_bytes` fail with `INPUT_TOO_LARGE`; they are never
split. The client retries only busy Jev responses (`429`, `502`, `529`), up to
the configured number of attempts. Other transport or response failures raise
`JevCheckError` with a typed `code`.

`TYPESAFE_API_KEY` is read from the environment, then from the macOS Keychain.
The request payload uses sorted, compact UTF-8 JSON for the `state` and
`questions` input record.

## Question sets

`load_question_set(path)` reads the
`plan-anchoring/questions/1` JSON schema. `QuestionSet.expand(template,
subjects)` returns one choice question per subject, keyed as
`<template>:<subject id>`.

## Input record

`input_record(state, questions, input_tokens, None, 0)` records the SHA-256 of
the canonical Jev payload and Jev's reported input-token count. Jev does not
report prompt tokens or make tool calls, so those fields remain `null` and
`commands` is zero.

## Tests

Run the package tests with:

```sh
uv run --project . --with pytest pytest -q tests
```
