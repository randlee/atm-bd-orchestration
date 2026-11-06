import re
from pathlib import Path
from urllib.parse import urlparse


def test_readme_repository_links_are_absolute_github_urls() -> None:
    readme = Path(__file__).parents[1] / "README.md"
    text = readme.read_text(encoding="utf-8")
    links = {
        label: target
        for label, target in re.findall(r"\[([^]]+)\]\(([^)]+)\)", text)
    }

    for label in ("Getting going with atm-bd", "plugin README"):
        parsed = urlparse(links[label])
        assert parsed.scheme == "https"
        assert parsed.netloc == "github.com"
