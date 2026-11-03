"""Load a phase's configuration and inline its named templates."""
import tomllib
from pathlib import Path

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
            profile_path = config["profile_path"]
            if not isinstance(lead, str) or not lead:
                raise ValueError("missing phase lead")
            if not isinstance(profile_path, str) or not profile_path:
                raise ValueError("missing profile_path")
            root = file.parent.parent
            manifest = Path(profile_path)
            if not manifest.is_absolute():
                manifest = root / manifest
            from atm_bd_core.profile import TEMPLATES, LoadedProfile, load_profile

            loaded = load_profile(manifest)
            if not isinstance(loaded, LoadedProfile):
                return loaded
            if loaded.profile.name != actual:
                return Refusal(ErrorId.PROFILE_MISMATCH, path=str(manifest), profile=loaded.profile.name)
            values = []
            for kind in TEMPLATES.values():
                template = loaded.profile.templates[kind]
                full = loaded.path(template)
                values.append((str(full), str(loaded.root), full.read_bytes()))
            keys = [(k, v) for k, v in config.items() if isinstance(v, str)]
            return _phase_file(actual, lead, values, keys)
        except (OSError, ValueError, KeyError, TypeError, tomllib.TOMLDecodeError) as exc:
            return Refusal(ErrorId.PHASE_UNREADABLE, path=path, profile=profile, reason=str(exc))
