# pyright: strict
"""Identify installed sprint QA assignment contracts."""
from pathlib import Path
import re
import yaml
from typing import TypeGuard


def is_object_mapping(value: object) -> TypeGuard[dict[object, object]]:
    return isinstance(value, dict)


def qa_capable_reviewer(name: str, templates_dir: Path) -> bool:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name):
        return False
    path = templates_dir / f"{name}-assignment.json.j2"
    try:
        text = path.read_text(encoding="utf-8")
        front = text.split("---", 2)
        if len(front) != 3 or front[0].strip():
            return False
        data = yaml.safe_load(front[1])
    except (OSError, UnicodeError, yaml.YAMLError):
        return False
    if not is_object_mapping(data):
        return False
    required = data.get("required_variables")
    return isinstance(required, list) and all(key in required for key in ("branch", "commit", "worktree_path", "review_targets"))


def qa_capable_reviewers(templates_dir: Path) -> list[str]:
    suffix = "-assignment.json.j2"
    return sorted(name for path in templates_dir.glob(f"*{suffix}")
                  if qa_capable_reviewer(name := path.name.removesuffix(suffix), templates_dir))
