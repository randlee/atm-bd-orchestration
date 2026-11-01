# pyright: strict
"""Read and enforce the one orchestration profile selected by a phase."""
from __future__ import annotations

import tomllib
from pathlib import Path

from atm_bd_types import Error, ErrorDetail, ErrorKind, Profile
from result import Err, Ok, Result


def read_profile(phase_file: Path) -> Result[Profile]:
    """Read a phase profile; existing phase files default to full."""
    try:
        with phase_file.open("rb") as source:
            phase = tomllib.load(source)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return Err(Error(ErrorKind.CONFIG_INVALID, f"{phase_file}: {exc}",
                         "Create or repair the phase TOML file.",
                         ErrorDetail.IoFailed(str(phase_file), str(exc))))
    value = phase.get("profile", "full")
    if value == "full":
        return Ok(Profile.FULL)
    if value == "lite":
        return Ok(Profile.LITE)
    return Err(Error(ErrorKind.CONFIG_INVALID, f"invalid phase profile {value!r}",
                     "Set profile to 'full' or 'lite'.",
                     ErrorDetail.ConfigInvalid("profile", str(value))))


def require_profile(phase_file: Path, expected: Profile) -> Result[Profile]:
    """Refuse execution if the phase uses a different profile."""
    found = read_profile(phase_file)
    if isinstance(found, Err):
        return found
    if found.value != expected:
        return Err(Error(ErrorKind.PROFILE_MISMATCH, f"{phase_file}: phase profile does not match caller",
                         "Run the command belonging to the phase profile."))
    return found
