lint:
    cd apps/atm-bd-console && uv run --frozen ruff check src tests
    uv run --frozen --project apps/atm-bd-console pyright

test:
    cd apps/atm-bd-console && uv run --frozen pytest -q
    uv run --frozen --project apps/atm-bd-console pytest -q .github/scripts/tests
    cd plugins/atm-bd-orchestration && uv run --frozen --project ../../apps/atm-bd-console python tests/gen_manifest.py --check
    cd plugins/atm-bd-orchestration && uv run --frozen --project ../../apps/atm-bd-console python -m pytest -q -rs
