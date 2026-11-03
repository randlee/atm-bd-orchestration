"""BeadStore implemented by the beads-cache journal and snapshot API."""
from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

from ._cache_binding import cache_module as bd_cache_rs

from atm_bd_types import ErrorId, Refusal, Stage, Status
from atm_bd_types._core import patch_json, stack_of
from atm_bd_types._native import _bead, _layer, _stack


def _refusal(exc, phase: str, bead: str = ""):
    code = getattr(exc, "code", "")
    kind = {"BD_CACHE.NOT_FOUND": ErrorId.BEAD_NOT_FOUND,
            "BD_CACHE.PRECONDITION": ErrorId.BEAD_RACED}.get(code, ErrorId.CACHE_UNAVAILABLE)
    return Refusal(kind, phase=phase, bead=bead, reason=str(exc))


class CacheStore:
    def __init__(self, cache, phase: str):
        self.cache = cache
        self.phase = phase

    @staticmethod
    def for_phase(phase: str):
        try:
            cwd = Path.cwd()
            root = next((p for p in (cwd, *cwd.parents) if (p / ".beads").is_dir()), None)
            if root is None:
                return Refusal(ErrorId.CACHE_UNAVAILABLE, phase=phase,
                               reason=f"no .beads directory at or above {cwd}")
            binary = shutil.which("bd")
            if binary is None:
                raise FileNotFoundError("bd executable not found on PATH")
            return CacheStore(bd_cache_rs.Cache(str(root), bd_binary=binary, scopes=[phase]), phase)
        except (bd_cache_rs.CacheError, OSError, RuntimeError, ValueError) as exc:
            return _refusal(exc, phase)

    def _row(self, bead_id: str):
        return self.cache.get(bead_id)["row"]["bead"]

    def _convert(self, row):
        metadata = row.get("metadata") or {}
        labels = row.get("labels") or []
        status = {"open": Status.OPEN, "in_progress": Status.IN_PROGRESS, "blocked": Status.BLOCKED,
                  "deferred": Status.DEFERRED, "closed": Status.CLOSED}[row["status"]]
        stage_name = next((x[6:] for x in labels if x.startswith("stage:")), "other")
        stage = {"dev": Stage.DEV, "fix": Stage.FIX, "qa": Stage.QA, "stack": Stage.STACK}.get(stage_name, Stage.OTHER)
        view = self.cache.get(row["id"])["row"]
        open_blockers = view["blocked"]
        blocks_ids = [other["bead"]["id"] for other in self.cache.list(self.phase)["rows"]
                      if any(edge.get("type") == "blocks" and edge.get("depends_on_id") == row["id"]
                             for edge in other["bead"].get("dependencies", []))]
        stack = None
        if stage == Stage.STACK:
            stack = _stack([_layer(x["branch"], x["head"], x["pr"], x["base"])
                            for x in metadata.get("layers", [])])
        return _bead(row["id"], status, stage, row.get("assignee") or None,
                     open_blockers=open_blockers, blocks_ids=blocks_ids,
                     branch=metadata.get("branch", ""), stack_bead=metadata.get("stack_bead", ""),
                     sprint=metadata.get("sprint_bead", ""), phase=metadata.get("phase_bead", ""),
                     checked_bead=metadata.get("checked_bead"), stack=stack)

    def show(self, bead_id: str):
        try:
            return self._convert(self._row(bead_id))
        except (bd_cache_rs.CacheError, KeyError, TypeError, ValueError, OSError, RuntimeError) as exc:
            return _refusal(exc, self.phase, bead_id)

    def list(self, phase: str):
        try:
            return [self._convert(view["bead"]) for view in self.cache.list(phase)["rows"]]
        except (bd_cache_rs.CacheError, KeyError, TypeError, ValueError, OSError, RuntimeError) as exc:
            return _refusal(exc, phase)

    def ready(self, phase: str):
        try:
            return [self._convert(view["bead"]) for view in self.cache.ready(phase)["ready"]]
        except (bd_cache_rs.CacheError, KeyError, TypeError, ValueError, OSError, RuntimeError) as exc:
            return _refusal(exc, phase)

    def target_layer(self, qa_bead):
        try:
            row = self._row(qa_bead.id)
            meta = row.get("metadata") or {}
            checked = meta.get("checked_bead")
            if not checked:
                checked = next((edge["depends_on_id"] for edge in row.get("dependencies", [])
                                if edge.get("type") == "blocks" and self._row(edge["depends_on_id"])["status"] == "closed"), None)
            if checked is None:
                return Refusal(ErrorId.CACHE_UNAVAILABLE, phase=self.phase, bead=qa_bead.id,
                               reason=f"QA bead {qa_bead.id} has no checked bead or closed blocker")
            target = self._convert(self._row(checked))
            stack = self.show(target.stack_bead)
            if isinstance(stack, Refusal):
                return stack
            ledger = stack_of(stack)
            layer = next((x for x in ledger.layers if x.branch == target.branch), None) if ledger else None
            return layer or Refusal(ErrorId.STACK_NOT_RECORDED, branch=target.branch)
        except (bd_cache_rs.CacheError, KeyError, TypeError, ValueError, OSError, RuntimeError) as exc:
            return _refusal(exc, self.phase, qa_bead.id)

    def update(self, patch, actor: str):
        data = json.loads(patch_json(patch))
        operation = data["operation"]
        value = data["value"]
        args = {"assign": {"assignee": value.get("agent")}, "start": {"status": "in_progress"},
                "reopen": {"status": "open", "assignee": ""},
                "close": {"reason": json.dumps(value, sort_keys=True, separators=(",", ":"))}}[operation]
        journaled = False
        try:
            written = self.cache.write(data["id"], "close" if operation == "close" else "update", args,
                             {"status": data["status"], "assignee": data["assignee"] or ""},
                             str(uuid.uuid4()), actor)
            journaled = True
            report = self.cache.drain(20, 25)
            entry = self.cache.entry(written["seq"])
            if entry["state"] == "applied":
                return None
            if any(item["seq"] == written["seq"] and item.get("reason", "").startswith("BD_CACHE.PRECONDITION:")
                   for item in report["escalated"]):
                return Refusal(ErrorId.BEAD_RACED, bead=data["id"])
            return Refusal(ErrorId.CACHE_UNAVAILABLE, phase=self.phase, bead=data["id"],
                           reason=f"write journaled; may still apply; re-check bead {data['id']} before retrying")
        except (bd_cache_rs.CacheError, KeyError, TypeError, ValueError, OSError, RuntimeError) as exc:
            if journaled:
                return Refusal(ErrorId.CACHE_UNAVAILABLE, phase=self.phase, bead=data["id"],
                               reason=f"write journaled; may still apply; re-check bead {data['id']} before retrying: {exc}")
            return _refusal(exc, self.phase, data["id"])
