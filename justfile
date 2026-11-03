lint:
    cd apps/atm-bd-console && uv run --frozen ruff check src tests
    uv run --frozen --project apps/atm-bd-console pyright
    cargo fmt --all --check
    cargo clippy --all-targets -- -D warnings
    cargo clippy --all-targets --features python -- -D warnings
    cd crates/atm-bd-types && uv run --frozen --no-editable ruff check .

# Provision the PEP 723 Python 3.11 script environment used by the offline runtime test.
warm-py311:
    uv run --python 3.11 --script plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/assignment-gates.py --help

# The last line builds the atm-bd-types abi3 wheel with maturin in isolation and runs the
# wheel tests: reply bytes, stub generation and contract diff, pyright strict on the lite hooks.
test:
    cd apps/atm-bd-console && uv run --frozen pytest -q
    uv run --frozen --project apps/atm-bd-console pytest -q .github/scripts/tests
    uv run --frozen --project apps/atm-bd-console python -m pytest -q tests/lite-gate-fixtures/test_gate.py
    cd plugins/atm-bd-orchestration && uv run --frozen --project ../../apps/atm-bd-console python tests/gen_manifest.py --check
    cd plugins/atm-bd-orchestration && uv run --frozen --project ../../apps/atm-bd-console python -m pytest -q -rs
    cd plugins/atm-bd-orchestration/tests/lite && uv run --frozen --project ../../../../apps/atm-bd-console python -m pytest -q -c /dev/null --rootdir . --confcutdir . .
    cargo test -p atm-bd-types
    cd crates/atm-bd-types && uv run --frozen --no-editable pytest -q
