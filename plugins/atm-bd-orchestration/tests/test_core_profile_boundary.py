"""Keep profile names out of framework source.

``core/tests`` is exempt because those tests run ``lite`` as a profile fixture
against the framework; that is test data, not framework code.
"""

import re
from pathlib import Path


PLUGIN = Path(__file__).resolve().parents[1]
CORE_SOURCE = PLUGIN / "core" / "atm_bd_core"
LITE_WORD = re.compile(r"\blite\b", re.IGNORECASE)


def test_framework_sources_do_not_name_a_profile() -> None:
    offenders = []
    for path in sorted(CORE_SOURCE.rglob("*")):
        relative = path.relative_to(CORE_SOURCE)
        if not path.is_file() or "tests" in relative.parts or path.name.startswith("test_"):
            continue
        if path.suffix not in {".py", ".toml"}:
            continue
        for line_number, line in enumerate(path.read_text().splitlines(), start=1):
            if LITE_WORD.search(line):
                offenders.append(f"{relative}:{line_number}: {line.strip()}")

    assert not offenders, "profile names found in framework sources:\n" + "\n".join(offenders)
