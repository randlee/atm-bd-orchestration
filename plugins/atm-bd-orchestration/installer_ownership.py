"""Classify existing files and back up replacements before an install."""
# pyright: strict
from __future__ import annotations

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from installer_common import BACKUP_DIR, CONFIG_TEMPLATE, PACKAGE, sha256


def ownership_state(
    key: str, data: bytes, pkg_rel: Optional[str], locked: dict[str, str],
    wanted: dict[str, tuple[bytes, bool, str]], pkg_dir: Path, legacy: dict[str, set[str]],
) -> Optional[bool]:
    """Return true for owned, false for foreign, and none for modified locked files."""
    digest = sha256(data)
    if key in locked:
        return True if locked[key] == digest else None
    if pkg_rel is None:
        return False
    shipped: set[str] = {sha256(wanted[key][0])} if key in wanted else set()
    src = pkg_dir / pkg_rel
    if src.is_file() and pkg_rel != CONFIG_TEMPLATE:
        shipped.add(sha256(src.read_bytes()))
    shipped |= legacy.get(pkg_rel, set())
    return digest in shipped


def backup_files(root: Path, paths: list[str]) -> None:
    """Move files selected by planning to a timestamped, ignored backup."""
    if not paths:
        return
    backup = root / BACKUP_DIR / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for key in paths:
        print(f"warning: {key} is modified or not {PACKAGE}'s; moved to {(backup / key).relative_to(root)}", file=sys.stderr)
        (backup / key).parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(root / key), str(backup / key))
    ignore = root / BACKUP_DIR / ".gitignore"
    if not ignore.exists():
        ignore.write_text("*\n")
