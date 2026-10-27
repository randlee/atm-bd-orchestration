from __future__ import annotations

import re
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]


def test_pypi_readme_links_are_absolute() -> None:
    # README.md is the PyPI long description; a relative link there resolves against pypi.org.
    text = (APP_ROOT / "README.md").read_text(encoding="utf-8")
    targets = re.findall(r"\]\(([^)\s]+)\)", text)
    assert targets
    relative = [target for target in targets if not target.startswith(("https://", "http://", "#", "mailto:"))]
    assert relative == []
