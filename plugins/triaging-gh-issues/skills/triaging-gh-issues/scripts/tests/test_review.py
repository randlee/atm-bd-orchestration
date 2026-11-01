"""QA gate for the skills and agents guidelines. A failure is a review miss."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
AGENTS = ROOT / "agents"
SKILL = ROOT / "skills" / "triaging-gh-issues" / "SKILL.md"
INSTALL = ROOT / "skills" / "triaging-gh-issues" / "references" / "installation-and-troubleshooting.md"
LIMIT = 3072
HEADINGS = (
    "## Check First",
    "## Find Existing Install",
    "## Install",
    "## Minimum Version",
    "## PATH Troubleshooting",
    "## Validation",
    "## Known Issues",
)


class Review(unittest.TestCase):
    def test_agents_stay_short_and_return_one_json_determination(self) -> None:
        files = sorted(AGENTS.glob("*.md"))
        self.assertEqual(len(files), 20)
        for path in files:
            text = path.read_text(encoding="utf-8")
            self.assertLess(path.stat().st_size, LIMIT, path.name)
            self.assertIn("version: 1.0.0", text, path.name)
            self.assertIn("```json", text, path.name)
            self.assertIn('"determination"', text, path.name)
            self.assertLess(text.count("## "), 8, path.name)

    def test_skill_is_a_dispatch_table(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        self.assertLess(SKILL.stat().st_size, LIMIT)
        self.assertIn("## Step 1 — Verify CLI Installation", text)
        self.assertIn("installation-and-troubleshooting.md", text)
        self.assertNotIn("## Purpose", text)
        self.assertNotIn("You are", text)

    def test_install_doc_has_the_required_sections(self) -> None:
        text = INSTALL.read_text(encoding="utf-8")
        for heading in HEADINGS:
            self.assertIn(heading, text)

    def test_registry_matches_agent_files(self) -> None:
        listed = (AGENTS / "registry.yaml").read_text(encoding="utf-8")
        for path in sorted(AGENTS.glob("*.md")):
            self.assertIn(f"path: agents/{path.name}", listed)
            self.assertIn("version: 1.0.0", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
