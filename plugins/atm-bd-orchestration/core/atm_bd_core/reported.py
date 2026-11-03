"""Own the report deduplication ledger and its persistence."""

import json
import os

from atm_bd_types import CollectError, FactKind


REPORTED_KEYS = "reported-keys.json"


def path_for(state_dir):
    return state_dir / REPORTED_KEYS


def reported_keys(state_dir):
    path = path_for(state_dir)
    try:
        try:
            content = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return [], None
        keys = json.loads(content)
        if not isinstance(keys, list) or any(not isinstance(key, str) for key in keys):
            raise ValueError("expected a JSON list of strings")
        return keys, None
    except (OSError, UnicodeError, ValueError) as error:
        return None, CollectError(FactKind.REPORTED_KEYS, [], str(error), f"Repair or restore {path}.")


def append(state_dir, keys, key):
    """Append a sent key and atomically persist the current ledger."""
    keys.append(key)
    path = path_for(state_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(keys, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)
