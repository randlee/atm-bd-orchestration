"""Repository requirement text that the package prompts follow."""
from pathlib import Path

DOCS = Path(__file__).resolve().parents[3] / "docs" / "requirements"


def test_quality_mgr_requirement_leaves_upstream_owned_content_to_the_lead():
    """#5: requirement 44 puts upstream-owned installed .claude/ content out of QA reviewer scope."""
    text = (DOCS / "quality-mgr.md").read_text()
    assert ("44. Upstream-owned installed `.claude/` skill, agent and template content is out of QA reviewer scope; "
            "the lead accepts such changes by diff review and the package's template tests.") in text
