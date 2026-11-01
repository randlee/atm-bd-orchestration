# pyright: strict
"""The phase profile defaults to full and mismatches are typed failures."""
from pathlib import Path

from atm_bd_types import ErrorKind, Profile
from phase_profile import read_profile, require_profile
from result import Err, Ok


def test_profile_defaults_and_mismatch(tmp_path: Path) -> None:
    phase = tmp_path / "phase.toml"
    phase.write_text('lead = "team"\n')
    found = read_profile(phase)
    assert isinstance(found, Ok) and found.value == Profile.FULL
    phase.write_text('profile = "lite"\n')
    found = require_profile(phase, Profile.FULL)
    assert isinstance(found, Err)
    assert found.error.kind == ErrorKind.PROFILE_MISMATCH
    assert found.error.fix
    assert isinstance(require_profile(phase, Profile.LITE), Ok)


def test_bad_or_missing_profile_file_is_a_typed_error(tmp_path: Path) -> None:
    phase = tmp_path / "phase.toml"
    missing = read_profile(phase)
    assert isinstance(missing, Err) and missing.error.kind == ErrorKind.CONFIG_INVALID
    phase.write_text('profile = "both"\n')
    invalid = read_profile(phase)
    assert isinstance(invalid, Err) and invalid.error.kind == ErrorKind.CONFIG_INVALID
