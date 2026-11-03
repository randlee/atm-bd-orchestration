"""Deterministic embedded beads fixtures shared by framework store tests."""
import json
import os
from pathlib import Path
import subprocess

BD_TIMEOUT_SECONDS = 30


def bd(root: Path, *args: str) -> str:
    command = [os.environ.get("ATM_TEST_BD", "bd"), *args]
    try:
        result = subprocess.run(
            command,
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=BD_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(f"bd command timed out after {BD_TIMEOUT_SECONDS}s: {command!r}") from error
    return result.stdout


def init_db(root: Path) -> None:
    bd(root, "init", "--prefix", "tst", "--non-interactive", "--quiet")


def create_bead(root: Path, bead_id: str, title: str, labels: str, metadata: dict) -> None:
    bd(root, "create", title, "--id", bead_id, "--labels", labels, "--metadata", json.dumps(metadata))
