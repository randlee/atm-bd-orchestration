"""Load the package test setup when pytest chooses core/ as its root directory."""
import runpy
from pathlib import Path

package = Path(__file__).resolve().parents[1]
setup = runpy.run_path(str(package / "conftest.py"))
collect_ignore = [path.removeprefix("tests/") for path in setup["collect_ignore"] if path.startswith("tests/")]
