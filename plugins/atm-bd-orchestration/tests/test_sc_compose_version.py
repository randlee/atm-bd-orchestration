"""The sc-compose CLI and the wheel the scripts run with are one version, in the manifest's supported range.

It runs in CI too, which installs the newest release (SC_COMPOSE_VERSION in .github/workflows/tests.yml, the version the
script runtime resolves); locally it checks the installed release. A new upstream release fails it until the pin moves.
"""
from __future__ import annotations

import subprocess

import install


def test_sc_compose_cli_and_script_runtime_wheel_are_one_supported_version():
    floor, ceiling = install.sc_compose_range()
    cli = subprocess.run(["sc-compose", "--version"], capture_output=True, text=True, check=True).stdout.split()[-1]
    # The scripts run under `uv run --script` with SCRIPT_HEADER, so that runtime's wheel is the one that counts.
    wheel = install.script_runtime_sc_compose_version()
    assert install.sc_compose_supported(cli) and cli == wheel, (
        f"the package needs the sc-compose CLI and the script runtime's wheel at one version >= {floor}, < {ceiling}; "
        f"CLI {cli}, wheel {wheel}. Install {install.sc_compose_upgrade()}.")
