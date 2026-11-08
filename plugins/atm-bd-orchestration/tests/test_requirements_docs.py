"""Repository requirement text that the package prompts follow."""
from pathlib import Path

DOCS = Path(__file__).resolve().parents[3] / "docs" / "requirements"


def requirement_statement(document: str, identifier: str) -> str:
    """The Requirement Statement prose of one Raptor REQ record in a role document."""
    record = document.split(f"\n## {identifier}: ", 1)[1].split("\n## ", 1)[0]
    section = record.split("\n### Requirement Statement\n", 1)[1]
    return section.split("\n**MUST statements:**", 1)[0].strip()


def test_quality_mgr_requirement_leaves_upstream_owned_content_to_the_lead():
    """#5: REQ-QM-0044 puts upstream-owned installed .claude/ content out of QA reviewer scope."""
    text = (DOCS / "quality-mgr.md").read_text()
    assert requirement_statement(text, "REQ-QM-0044") == (
        "Upstream-owned installed `.claude/` skill, agent and template content is out of QA reviewer scope; "
        "the lead accepts such changes by diff review and the package's template tests.")
