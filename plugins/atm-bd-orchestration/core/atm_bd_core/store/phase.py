"""Load a phase's configuration and inline its named templates."""
from pathlib import Path
import tomllib

from atm_bd_types import ErrorId, Refusal
from atm_bd_types._native import _phase_file


class PhaseFilesCli:
    def load(self, path: str, profile: str):
        try:
            file = Path(path).resolve()
            with file.open("rb") as source:
                config = tomllib.load(source)
            actual = config.get("profile")
            if actual is None:
                return Refusal(ErrorId.PROFILE_MISMATCH, path=path, profile=profile,
                               reason=f'add profile = "{profile}" to {path}')
            if actual != profile:
                return Refusal(ErrorId.PROFILE_MISMATCH, path=path, profile=profile)
            lead = config["lead"]
            templates = config["templates"]
            if not isinstance(lead, str) or not lead:
                raise ValueError("missing phase lead")
            root = file.parent.parent
            values = []
            for name in ("refuse", "dev-close", "qa-pass", "qa-findings", "land-close"):
                template = templates[name]
                if not isinstance(template, str) or not template:
                    raise ValueError(f"invalid template {name}")
                full = (root / template).resolve()
                values.append((template, str(root), full.read_bytes()))
            keys = [(k, v) for k, v in config.items() if isinstance(v, str)]
            return _phase_file(actual, lead, values, keys)
        except (OSError, ValueError, KeyError, TypeError, tomllib.TOMLDecodeError) as exc:
            return Refusal(ErrorId.PHASE_UNREADABLE, path=path, profile=profile, reason=str(exc))
