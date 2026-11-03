#!/usr/bin/env python3
"""Run one gate per declared hook in each plug-in profile."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    gate = Path(__file__).with_name("atm-bd-lite-gate.py")
    count = 0
    status = 0
    output_dir = Path(tempfile.mkdtemp(prefix="atm-hook-gate-"))
    for profile in sorted((root / "skills").glob("*/profile.toml")):
        data = tomllib.loads(profile.read_text(encoding="utf-8"))
        for hook, script in sorted(data.get("hooks", {}).items()):
            spec = profile.parent / "hooks" / (hook.replace(".", "-") + ".md")
            if not spec.is_file():
                print(f"GATE.SPEC_MISSING: {spec}", file=sys.stderr)
                status = 2
                continue
            result = subprocess.run([sys.executable, str(gate), str(profile.parent / script), str(spec),
                                     "--out", str(output_dir / f"{profile.parent.name}-{hook}.json")],
                                    check=False)
            if result.returncode:
                status = max(status, result.returncode)
            count += 1
    if count == 0:
        print("GATE.NO_HOOKS: no declared plug-in hooks found", file=sys.stderr)
        return 2
    return status


if __name__ == "__main__":
    sys.exit(main())
