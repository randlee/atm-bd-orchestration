from pathlib import Path

from qa_reviewers import qa_capable_reviewer, qa_capable_reviewers

TEMPLATES = Path(__file__).parents[2] / "templates"


def test_only_sprint_qa_contracts_qualify():
    for name in ("team-lead", "rust-developer", "dev-sanity", "plan-scope-reviewer", "../flaky-test-qa"):
        assert not qa_capable_reviewer(name, TEMPLATES)
    assert qa_capable_reviewer("flaky-test-qa", TEMPLATES)
    assert "flaky-test-qa" in qa_capable_reviewers(TEMPLATES)
