"""Read report deduplication state without modifying it."""

import json

from atm_bd_types import CollectError, FactKind


def reported_keys(state_dir):
    path = state_dir / "reported-keys.json"
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
