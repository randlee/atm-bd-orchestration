# pyright: strict
"""Persist provider-enriched ATM vars without modifying the dispatch input."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

import json as _core_json
import sys as _core_sys
from pathlib import Path as _CorePath
_core = next((candidate for parent in _CorePath(__file__).resolve().parents
              for candidate in (parent / ".atm-bd/scripts", parent / "plugins/atm-bd-orchestration/core/scripts")
              if (candidate / "core_paths.py").is_file()), None)
if _core is None:
    print(_core_json.dumps({"err": {"code": "CORE.NOT_FOUND", "fix": "run atm-bd skill --dest <repository>"}}), file=_core_sys.stderr)
    raise SystemExit(3)
_core_sys.path.insert(0, str(_core))
import core_paths as _core_paths  # noqa: E402
from result import Err as _CoreErr  # noqa: E402
_core_resolved = _core_paths.core_scripts_dir(_CorePath(__file__))
if isinstance(_core_resolved, _CoreErr):
    print(_core_json.dumps({"err": {"code": "CORE.NOT_FOUND", "fix": _core_resolved.error.fix}}), file=_core_sys.stderr)
    raise SystemExit(3)

from atm_bd_types import Error, ErrorKind
from providers import render_context
from result import Err, Ok, Result


def enrich_atm_vars(argv: Sequence[str], config: Mapping[str, object], dispatch_path: Path,
                    task: str) -> Result[list[str]]:
    """Persist one deterministic vars snapshot per task and ATM operation."""
    args = list(argv)
    if not args or args[0] != "atm" or "--vars" not in args:
        return Ok(args)
    index = args.index("--vars") + 1
    if index >= len(args):
        return Err(Error(ErrorKind.CONFIG_INVALID, "ATM --vars has no path", "Supply the vars file path."))
    provider = render_context(config)
    if isinstance(provider, Err):
        return provider
    try:
        raw: object = json.loads(Path(args[index]).read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return Err(Error(ErrorKind.CONFIG_INVALID, "ATM vars must be a JSON object", "Supply a JSON object as the vars file."))
        payload = cast(dict[str, object], raw)
        payload["provider"] = provider.value
        stable_argv = list(args)
        stable_argv[index] = "<vars>"
        digest = hashlib.sha256(json.dumps([task, stable_argv]).encode()).hexdigest()[:16]
        path = dispatch_path.with_name(f"{dispatch_path.stem}.{digest}.provider.json")
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(payload, stream)
            os.replace(temporary, path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        args[index] = str(path)
        return Ok(args)
    except (OSError, UnicodeError, ValueError, TypeError) as error:
        return Err(Error(ErrorKind.IO_FAILED, str(error), "Check the vars file and its directory, then retry."))
