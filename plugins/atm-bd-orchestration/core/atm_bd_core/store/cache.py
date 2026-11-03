"""BeadStore implemented by the beads-cache journal and snapshot API."""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from ._cache_binding import cache_module as bd_cache_rs

from atm_bd_types import ErrorId, PatchKind, Refusal, Stage, Status
from atm_bd_types._core import encode_evidence, stack_of
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
    def for_phase(phase: str) -> CacheStore | Refusal:
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

    def _view(self, bead_id: str):
        return self.cache.get(bead_id)["row"]

    def _row(self, bead_id: str):
        return self._view(bead_id)["bead"]

    def _views(self, phase: str):
        rows = self.cache.list(phase)["rows"]
        return [self._view(row["bead"]["id"]) for row in rows]

    @staticmethod
    def _blocks_index(views):
        index: dict[str, list[str]] = {}
        for view in views:
            bead = view["bead"]
            for edge in bead.get("dependencies", []):
                if edge.get("type") == "blocks":
                    index.setdefault(edge.get("depends_on_id"), []).append(bead["id"])
        return index

    def _convert(self, view, blocks_index):
        row = view["bead"]
        metadata = row.get("metadata") or {}
        labels = row.get("labels") or []
        status = Status.parse(row["status"])
        if status is None:
            raise ValueError(f"unknown bead status {row['status']!r}")
        stage_name = next((x[6:] for x in labels if x.startswith("stage:")), "other")
        stage = Stage.parse(stage_name)
        open_blockers = view["blocked"]
        blocks_ids = blocks_index.get(row["id"], [])
        stack = None
        if stage == Stage.STACK:
            stack = _stack([_layer(x["branch"], x["head"], x["pr"], x.get("base") or None)
                            for x in metadata.get("layers", [])])
        return _bead(row["id"], status, stage, row.get("assignee") or None,
                     open_blockers=open_blockers, blocks_ids=blocks_ids,
                     branch=metadata.get("branch") or None, stack_bead=metadata.get("stack_bead") or None,
                     sprint=metadata.get("sprint_bead") or None, phase=metadata.get("phase_bead") or None,
                     checked_bead=metadata.get("checked_bead"), stack=stack)

    def refresh(self, bead_ids: list[str]):
        try:
            self.cache.refresh(bead_ids, 20)
            return None
        except (bd_cache_rs.CacheError, KeyError, TypeError, ValueError, OSError, RuntimeError) as exc:
            return _refusal(exc, self.phase)

    def show(self, bead_id: str | None):
        if bead_id is None:
            return Refusal(ErrorId.STACK_NOT_RECORDED, phase=self.phase, branch="")
        try:
            view = self._view(bead_id)
            if "stage:stack" in (view["bead"].get("labels") or []):
                if (error := self.refresh([bead_id])) is not None:
                    return error
                view = self._view(bead_id)
            views = self._views(self.phase)
            return self._convert(view, self._blocks_index(views))
        except (bd_cache_rs.CacheError, KeyError, TypeError, ValueError, OSError, RuntimeError) as exc:
            return _refusal(exc, self.phase, bead_id)

    def list(self, phase: str):
        try:
            views = self._views(phase)
            blocks_index = self._blocks_index(views)
            return [self._convert(view, blocks_index) for view in views]
        except (bd_cache_rs.CacheError, KeyError, TypeError, ValueError, OSError, RuntimeError) as exc:
            return _refusal(exc, phase)

    def ready(self, phase: str):
        try:
            ready = self.cache.ready(phase)["ready"]
            views = self._views(phase)
            blocks_index = self._blocks_index(views)
            views_by_id = {view["bead"]["id"]: view for view in views}
            return [self._convert(views_by_id[row["bead"]["id"]], blocks_index) for row in ready]
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
            target_view = self._view(checked)
            blocks_index = self._blocks_index(self._views(self.phase))
            target = self._convert(target_view, blocks_index)
            if target.stack_bead is None or target.branch is None:
                return Refusal(ErrorId.STACK_NOT_RECORDED, branch=target.branch or "")
            stack = self.show(target.stack_bead)
            if isinstance(stack, Refusal):
                return stack
            ledger = stack_of(stack)
            layer = next((x for x in ledger.layers if x.branch == target.branch), None) if ledger else None
            return layer or Refusal(ErrorId.STACK_NOT_RECORDED, branch=target.branch)
        except (bd_cache_rs.CacheError, KeyError, TypeError, ValueError, OSError, RuntimeError) as exc:
            return _refusal(exc, self.phase, qa_bead.id)

    def update(self, patch, actor: str):
        try:
            if patch.kind == PatchKind.ASSIGN:
                args = {"assignee": patch.agent}
            elif patch.kind == PatchKind.START:
                args = {"status": Status.IN_PROGRESS.as_str()}
            elif patch.kind == PatchKind.REOPEN:
                args = {"status": Status.OPEN.as_str(), "assignee": ""}
            elif patch.kind == PatchKind.CLOSE:
                args = {"reason": encode_evidence(patch.evidence)}
            else:
                raise ValueError(f"unsupported patch kind {patch.kind!r}")
            operation = "close" if patch.kind == PatchKind.CLOSE else "update"
            self.cache.write(patch.bead_id, operation, args,
                             {"status": patch.expected_status.as_str(), "assignee": patch.expected_assignee or ""},
                             str(uuid.uuid4()), actor)
            return None
        except (bd_cache_rs.CacheError, KeyError, TypeError, ValueError, OSError, RuntimeError) as exc:
            return _refusal(exc, self.phase, patch.bead_id)

    def drain(self):
        """Apply pending writes and return this phase's unannounced escalations."""
        self.cache.drain(20, 25)
        return [item for item in self.cache.unannounced_escalations() if item.get("phase") == self.phase]

    def mark_announced(self, seq: int):
        self.cache.mark_announced(seq)
