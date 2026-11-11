# Plug-in hook gate

`run-plugin-gates.py` runs deterministic checks and reads a committed Jev record for each hook. CI never calls Jev. A
missing record or any recorded answer other than `yes` fails the gate and reports the hook and input SHA-256.

The record key hashes the exact hook source, its spec, and `gate-questions.json`. After changing any of those inputs,
record one new Jev sample with:

```sh
uv run --no-project --with 'pydantic>=2' --with pyyaml --with 'sc-compose>=1.8.0,<2' \
  python plugins/atm-bd-orchestration/core/gate/record-plugin-gates.py
```

The command reads `TYPESAFE_API_KEY` from the environment first, then the macOS Keychain entry named
`TYPESAFE_API_KEY`. It writes records under `jev-records/` and refuses to replace an existing sample for the same hash.
Review and commit the new record with the hook or spec change. A `no` answer stays failing until the hook, spec, or
question set changes and produces a new hash.
