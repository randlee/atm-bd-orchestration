"""Phase template paths come from the selected profile manifest."""
from pathlib import Path

from atm_bd_core.profile import TEMPLATES
from atm_bd_core.store import PhaseFilesCli
from atm_bd_types import PhaseFile


def test_phase_files_load_templates_from_profile_path(tmp_path: Path) -> None:
    profile_root = tmp_path / "profile"
    templates_dir = profile_root / "templates"
    templates_dir.mkdir(parents=True)
    template_paths = {}
    template_lines = []
    for name, kind in TEMPLATES.items():
        relative = f"templates/{name}.j2"
        path = profile_root / relative
        path.write_text(f"{name} template", encoding="utf-8")
        template_paths[kind] = str(path.resolve())
        template_lines.append(f'{name} = "{relative}"')
    (profile_root / "policy.toml").write_text("[params]\n", encoding="utf-8")
    manifest = profile_root / "profile.toml"
    manifest.write_text(
        'name = "lite"\nstages = ["dev"]\npolicy = "policy.toml"\n[hooks]\n[templates]\n'
        + "\n".join(template_lines)
        + "\n",
        encoding="utf-8",
    )
    phase_path = tmp_path / ".atm-bd" / "phase-bo.toml"
    phase_path.parent.mkdir()
    phase_path.write_text(
        'profile = "lite"\nprofile_path = "profile/profile.toml"\nlead = "phase-lead"\n',
        encoding="utf-8",
    )

    phase = PhaseFilesCli().load(str(phase_path), "lite")

    assert isinstance(phase, PhaseFile), phase
    for kind, path in template_paths.items():
        assert phase.template(kind) == path
