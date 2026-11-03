"""ATM cron wire adapter for a profile's framework tick."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from atm_bd_types import Refusal, Status

from atm_bd_core.profile import load_profile
from atm_bd_core.store import CacheStore, PhaseFilesCli
from atm_bd_core.tick import phase_paths, tick

CRON_TIMEOUT_MS = 30000


def handle(envelope: dict) -> dict:
    hook, phase = envelope["hook"], envelope["phase"]
    args = envelope["request"]["args"]
    if len(args) != 2 or not all(isinstance(arg, str) for arg in args):
        raise ValueError("cron requires profile path and primary checkout arguments")
    profile, primary = Path(args[0]), Path(args[1])
    if hook == "cron.tick":
        result = tick(profile, phase, primary)
        return ({"result": "refused", "message": repr(result)} if isinstance(result, Refusal)
                else {"result": "pass-through"})
    if hook != "cron.stop":
        raise ValueError(f"unsupported hook {hook}")
    loaded = load_profile(profile)
    if isinstance(loaded, Refusal):
        raise RuntimeError(repr(loaded))
    config = PhaseFilesCli().load(str(phase_paths(primary, phase)[0]), loaded.profile.name)
    if isinstance(config, Refusal):
        raise RuntimeError(repr(config))
    root = config.key("root")
    if not root:
        raise ValueError("phase file has no root bead")
    cache = CacheStore.for_phase(phase)
    if isinstance(cache, Refusal):
        raise RuntimeError(repr(cache))
    # ADR-069 D4 makes the phase root's closure the mandatory atm-bd cron stop condition.
    bead = cache.show(root)
    if isinstance(bead, Refusal):
        raise RuntimeError(repr(bead))
    return {"stop": True, "reason": "phase closed"} if bead.status == Status.CLOSED else {"stop": False}


def main() -> None:
    try:
        print(json.dumps(handle(json.load(sys.stdin))))
    except (KeyError, TypeError, ValueError, OSError, RuntimeError) as exc:
        print(f"cron entry: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
