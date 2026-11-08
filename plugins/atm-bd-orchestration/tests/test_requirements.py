from pathlib import Path

from test_requirements_docs import requirement_statement


PLUGIN = Path(__file__).resolve().parents[1]
REPOSITORY = Path(__file__).resolve().parents[3]


def test_sanity_guidance_does_not_render_deleted_run_table():
    for path in (PLUGIN / "agents/dev-sanity.md", REPOSITORY / "docs/requirements/dev-sanity.md"):
        assert "sanity-run-table.md.j2" not in path.read_text()


def test_close_hook_requirement_distinguishes_bd_and_atm_identity():
    requirement = (REPOSITORY / "docs/requirements/task-close-hook.md").read_text()
    identity = requirement_statement(requirement, "REQ-TCH-0004")
    assert '`bd` writes carry `--actor "$ATM_IDENTITY"`' in identity
    assert "`atm` writes take `ATM_IDENTITY` from the environment" in identity
