"""Deterministic embedded beads fixtures shared by framework store tests."""
import json
import os
from pathlib import Path
import subprocess


def bd(root: Path, *args: str) -> None:
    subprocess.run([os.environ.get("ATM_TEST_BD", "bd"), *args], cwd=root, check=True, capture_output=True, text=True)


def init_db(root: Path) -> None:
    bd(root, "init", "--prefix", "tst", "--non-interactive", "--quiet")


def create_bead(root: Path, bead_id: str, title: str, labels: str, metadata: dict) -> None:
    bd(root, "create", title, "--id", bead_id, "--labels", labels, "--metadata", json.dumps(metadata))
