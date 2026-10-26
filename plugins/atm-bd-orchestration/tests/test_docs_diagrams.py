"""The workflow diagrams show every sanity-stack-link result and the fix-round rule (#482, #480)."""
import re
import shutil
import subprocess
from pathlib import Path

import pytest

DOCS = Path(__file__).resolve().parents[3] / "docs"
README = DOCS / "requirements" / "README.md"
LIFECYCLE = DOCS / "diagrams" / "lifecycle.md"
NOT_STACKED = ("rebase_required", "lock_timeout", "stack_failed")


def mermaid(path):
    return re.findall(r"```mermaid\n(.*?)```", path.read_text(), re.S)


def test_readme_flowchart_has_one_edge_per_stack_result():
    chart = next(block for block in mermaid(README) if "sanity-stack-link" in block)
    edges = re.findall(r'^\s*SL -->\|"([^"]*)"\|\s*(\w+)', chart, re.M)
    labels = {label.split(":")[0]: target for label, target in edges}
    assert labels.keys() == {"stacked", *NOT_STACKED}
    assert labels["stacked"] != labels["rebase_required"]
    for result in NOT_STACKED:
        assert labels[result] == "L2"
        assert f"{result}: notify the lead" in chart
    assert "the sanity task stays closed" in chart
    assert '-->|"not fixed: pour round n+1, nothing reopened"| F' in chart


def test_lifecycle_has_a_branch_per_stack_result():
    chart = mermaid(LIFECYCLE)[0]
    branches = re.findall(r"^\s*(?:alt|else) (\w+)\s*\n\s*S->>(\w+): (.*)$", chart, re.M)
    by_result = {result: (target, text) for result, target, text in branches}
    assert by_result.keys() >= {"stacked", *NOT_STACKED}
    for result in NOT_STACKED:
        assert by_result[result] == ("L", "notify the lead, sanity stays closed")
    assert not [line for line in chart.splitlines() if line.strip().startswith("Note") and ";" in line]


@pytest.mark.skipif(shutil.which("mmdflux") is None, reason="mmdflux not on PATH")
@pytest.mark.parametrize("path", [README, LIFECYCLE], ids=lambda p: p.name)
def test_diagrams_parse(path, tmp_path):
    for n, block in enumerate(mermaid(path)):
        source = tmp_path / f"{n}.mmd"
        source.write_text(block)
        result = subprocess.run(["mmdflux", "--format", "text", str(source)], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
