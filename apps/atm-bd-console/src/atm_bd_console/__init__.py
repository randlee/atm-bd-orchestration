"""Shared contract for the ATM bead dashboard."""

__version__ = "0.19.12"

# The installed wheel bundles the same core used by repository installs.
import importlib
import json
import sys
from pathlib import Path

_here = Path(__file__).resolve()
_candidates = [parent / "plugins/atm-bd-orchestration/core/scripts" for parent in _here.parents]
_candidates.insert(0, _here.parent / "_skills/core/scripts")
_core = next((path for path in _candidates if (path / "core_paths.py").is_file()), None)
if _core is None:
    print(json.dumps({"err": {"code": "CORE.NOT_FOUND", "fix": "Run atm-bd skill --dest <repository> to install atm-bd core"}}), file=sys.stderr)
    raise SystemExit(3)
sys.path.insert(0, str(_core))
_core_paths = importlib.import_module("core_paths")
_result = importlib.import_module("result")
_resolved = _core_paths.core_scripts_dir(_core)
if isinstance(_resolved, _result.Err):
    print(json.dumps({"err": {"code": "CORE.NOT_FOUND", "fix": _resolved.error.fix}}), file=sys.stderr)
    raise SystemExit(3)
sys.modules[__name__ + ".result"] = _result
