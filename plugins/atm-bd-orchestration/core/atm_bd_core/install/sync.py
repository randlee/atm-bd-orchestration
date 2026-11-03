"""Initialize a phase cache before exposing its hooks to ATM."""
import shutil
import sys

from atm_bd_core.store._cache_binding import cache_module


def main() -> None:
    root, phase = sys.argv[1:]
    binary = shutil.which("bd")
    if binary is None:
        raise SystemExit("bd executable not found on PATH")
    cache = cache_module.Cache(root, bd_binary=binary, scopes=[phase])
    try:
        result = cache.sync(phase, 20)
        if result.get("outage") or result.get("deferred") or not result.get("model_current"):
            raise SystemExit(f"phase cache sync incomplete: {result}")
    finally:
        cache.close()


if __name__ == "__main__":
    main()
