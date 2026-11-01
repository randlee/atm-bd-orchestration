import os
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]


def test_publish_uses_release_assets_and_separate_targets():
    workflow = yaml.safe_load((ROOT / ".github/workflows/pypi-publish.yml").read_text())
    assert workflow[True]["workflow_dispatch"]["inputs"]["target"]["options"] == ["testpypi", "production"]
    assert workflow["jobs"]["publish"]["needs"] == ["verify-release", "publish-types"]
    types = workflow["jobs"]["publish-types"]
    assert types["needs"] == "verify-release"
    assert types["if"] == "${{ inputs.target == 'production' }}"
    assert types["uses"] == "./.github/workflows/crate-release.yml"
    assert types["with"]["release_ref"] == "${{ inputs.tag }}"
    condition = workflow["jobs"]["publish"]["if"]
    assert "needs.publish-types.result == 'success'" in condition
    assert "inputs.target == 'testpypi'" in condition
    steps = workflow["jobs"]["publish"]["steps"]
    script = "\n".join(step.get("run", "") for step in steps)
    assert "gh release download" in script
    assert "verify-python-release-assets" in script
    assert "python -m twine upload" in script
    assert "--skip-existing" in script
    assert "uv publish" not in script
    assert "python -m build" not in script


def test_types_release_uses_the_release_ref_and_repository_version():
    workflow = yaml.safe_load((ROOT / ".github/workflows/crate-release.yml").read_text())
    calls = workflow[True]["workflow_call"]
    assert set(calls["inputs"]) == {"release_ref"}
    assert workflow[True]["workflow_dispatch"] is None
    jobs = workflow["jobs"]
    assert jobs["crate"]["needs"] == "wheels"
    assert jobs["pypi"]["needs"] == ["wheels", "crate"]
    for name in ("wheels", "crate"):
        checkout = next(step for step in jobs[name]["steps"] if step.get("uses", "").startswith("actions/checkout@"))
        assert checkout["with"]["ref"] == "${{ inputs.release_ref || github.sha }}"
        assert any("release-version.toml" in step.get("run", "") for step in jobs[name]["steps"])


@pytest.mark.parametrize(("status", "yanked", "expected", "publishes"), [
    ("404", "false", 0, True), ("200", "false", 0, False),
    ("200", "true", 1, False), ("503", "false", 1, False),
])
def test_crate_publication_retries_only_confirmed_absence(tmp_path, status, yanked, expected, publishes):
    workflow = yaml.safe_load((ROOT / ".github/workflows/crate-release.yml").read_text())
    script = next(step["run"] for step in workflow["jobs"]["crate"]["steps"] if step.get("name") == "Validate version and publish crate")
    (tmp_path / "release-version.toml").write_text('[project]\nversion = "1.2.3"\n')
    crate = tmp_path / "crates/atm-bd-types"
    crate.mkdir(parents=True)
    (crate / "Cargo.toml").write_text('[package]\nversion = "1.2.3"\n')
    curl = tmp_path / "curl"
    curl.write_text('#!/bin/sh\nprintf \'{"version":{"yanked":%s}}\' "$TEST_YANKED" > "$RUNNER_TEMP/crate.json"\nprintf %s "$TEST_STATUS"\n')
    curl.chmod(0o755)
    cargo = tmp_path / "cargo"
    cargo.write_text('#!/bin/sh\nprintf %s "$*" > "$RUNNER_TEMP/published"\n')
    cargo.chmod(0o755)
    env = {**os.environ, "PATH": f"{tmp_path}{os.pathsep}{os.environ['PATH']}", "RUNNER_TEMP": str(tmp_path),
           "TEST_STATUS": status, "TEST_YANKED": yanked}
    result = subprocess.run(["bash", "-c", script], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30, check=False)
    assert (result.returncode == 0) == (expected == 0), result.stderr
    assert (tmp_path / "published").exists() is publishes


def test_release_jobs_preserve_tagging_and_rehearsal_order():
    workflow = yaml.safe_load((ROOT / ".github/workflows/release.yml").read_text())
    jobs = workflow["jobs"]
    assert set(jobs) == {"gate-and-tag", "release-plan", "build-python-wheels",
                         "build-python-sdists", "publish-testpypi", "release"}
    for job in jobs.values():
        dependencies = job.get("needs", [])
        if isinstance(dependencies, str):
            dependencies = [dependencies]
        assert set(dependencies) <= set(jobs)
    gate = jobs["gate-and-tag"]["steps"]
    assert next(step for step in gate if step.get("id") == "candidate")["if"] == "${{ inputs.target == 'testpypi' }}"
    tag = next(step for step in gate if step.get("id") == "release-ref")["run"]
    assert 'git tag "$tag" "$main_sha"' in tag
    assert 'if [[ "$target" == "production" ]]' in tag
    rehearsal = jobs["publish-testpypi"]
    assert "release_target == 'testpypi'" in rehearsal["if"]
    assert rehearsal["environment"] == "testpypi"
    assert "release_target == 'production'" in jobs["release"]["if"]
    script = "\n".join(step.get("run", "") for step in rehearsal["steps"])
    assert "twine==6.1.0" in script and "twine upload" in script
    assert "gh release" not in script
    assert jobs["release"]["steps"][-1]["run"].endswith("--finalized")


def test_ci_checks_both_artifacts_with_the_publisher_twine():
    workflow = yaml.safe_load((ROOT / ".github/workflows/tests.yml").read_text())
    checks = [step["run"] for step in workflow["jobs"]["console-tests"]["steps"]
              if "python -m twine check" in step.get("run", "")]
    assert len(checks) == 1
    assert "python -m build --wheel --sdist" in checks[0]
    assert "--with twine==6.1.0" in checks[0]
    assert "*.whl" in checks[0] and "*.tar.gz" in checks[0]


def test_python_release_builds_keep_full_history_for_console_identity():
    workflow = yaml.safe_load((ROOT / ".github/workflows/release.yml").read_text())
    for name in ("build-python-wheels", "build-python-sdists"):
        checkout = next(step for step in workflow["jobs"][name]["steps"]
                        if step.get("uses", "").startswith("actions/checkout@"))
        assert checkout["with"]["fetch-depth"] == 0
    action = yaml.safe_load((ROOT / ".github/actions/setup-python-release-build/action.yml").read_text())
    checkout = next(step for step in action["runs"]["steps"]
                    if step.get("uses", "").startswith("actions/checkout@"))
    assert checkout["with"]["fetch-depth"] == 0


@pytest.mark.parametrize("mode,expected", [("absent", 1), ("auth", 1), ("complete", 0)])
def test_copied_release_verifier_fails_closed(tmp_path, mode, expected):
    action = yaml.safe_load((ROOT / ".github/actions/verify-published-release/action.yml").read_text())
    executable = tmp_path / "gh"
    executable.write_text("#!/bin/sh\ncase \"$PROBE_FIXTURE\" in\nabsent) echo 'HTTP 404' >&2; exit 1;;\nauth) echo 'HTTP 403' >&2; exit 1;;\ncomplete) echo '{\"isDraft\":false,\"assets\":[{\"name\":\"fixture.whl\"}]}' ;;\nesac\n")
    executable.chmod(0o755)
    result = subprocess.run(["bash", "-c", action["runs"]["steps"][0]["run"]],
                            env={**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}",
                                 "PROBE_FIXTURE": mode, "RELEASE_TAG": "v0.17.3",
                                 "RELEASE_REPOSITORY": "fixture/repo", "PROBE_MODE": "false",
                                 "REQUIRED_ASSET_PATTERNS": r"\.whl$", "GITHUB_OUTPUT": str(tmp_path / "outputs")},
                            text=True, capture_output=True, timeout=30, check=False)
    assert result.returncode == expected, result.stderr
