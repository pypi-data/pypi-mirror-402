from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import tempfile
from typing import Any


_STATE_DIRNAME = ".voidchat"
_RUN_FILENAME = "run.json"
_CONTEXT_TREE_FILENAME = "context-tree.json"
_MEMORY_DIRNAME = "memory"


@dataclass(frozen=True)
class WorkspacePaths:
    workspace: Path
    state_dir: Path
    run_path: Path
    context_tree_path: Path
    memory_dir: Path


@dataclass
class RunState:
    """Host-side run state persisted under <workspace>/.voidchat/run.json.

    Keep this intentionally minimal for WP-01/WP-02.
    """

    schema_version: int = 1
    workspace_label: str | None = None
    active_node_id: str | None = None
    active_node_alias: str | None = None
    pending_gate: bool = False
    next_action: str | None = None
    last_checkpoint: str | None = None


def resolve_workspace_path(*, workspace: str | None, cwd: Path | None = None) -> Path:
    base = (cwd or Path.cwd()).resolve()
    if workspace is None:
        return base
    raw = (workspace or "").strip()
    if not raw:
        return base
    # Allow relative path input; resolve to absolute path as the single truth.
    p = Path(os.path.expanduser(raw))
    if not p.is_absolute():
        p = (base / p).resolve()
    else:
        p = p.resolve()
    return p


def workspace_paths(workspace: Path) -> WorkspacePaths:
    ws = workspace.resolve()
    state_dir = ws / _STATE_DIRNAME
    return WorkspacePaths(
        workspace=ws,
        state_dir=state_dir,
        run_path=state_dir / _RUN_FILENAME,
        context_tree_path=state_dir / _CONTEXT_TREE_FILENAME,
        memory_dir=state_dir / _MEMORY_DIRNAME,
    )


def ensure_workspace_state_dirs(paths: WorkspacePaths) -> None:
    paths.state_dir.mkdir(parents=True, exist_ok=True)
    # Create placeholders for future steps; harmless even if unused now.
    paths.memory_dir.mkdir(parents=True, exist_ok=True)


def load_run_state(run_path: Path) -> RunState:
    try:
        if not run_path.is_file():
            return RunState()
        data = json.loads(run_path.read_text(encoding="utf-8"))
    except Exception:
        return RunState()

    if not isinstance(data, dict):
        return RunState()
    return RunState(
        schema_version=int(data.get("schema_version") or 1),
        workspace_label=(str(data.get("workspace_label")).strip() if data.get("workspace_label") else None),
        active_node_id=(str(data.get("active_node_id")).strip() if data.get("active_node_id") else None),
        active_node_alias=(str(data.get("active_node_alias")).strip() if data.get("active_node_alias") else None),
        pending_gate=bool(data.get("pending_gate", False)),
        next_action=(str(data.get("next_action")).strip() if data.get("next_action") else None),
        last_checkpoint=(str(data.get("last_checkpoint")).strip() if data.get("last_checkpoint") else None),
    )


def save_run_state(run_path: Path, state: RunState) -> None:
    run_path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = asdict(state)
    payload["schema_version"] = int(payload.get("schema_version") or 1)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    # Atomic-ish write: write to temp then replace.
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        delete=False,
        dir=str(run_path.parent),
        prefix=f".{run_path.name}.",
        suffix=".tmp",
    ) as handle:
        tmp_path = Path(handle.name)
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    tmp_path.replace(run_path)


def effective_workspace_label(*, workspace: Path, state: RunState) -> str:
    raw = (state.workspace_label or "").strip()
    return raw if raw else workspace.resolve().name


def render_where(
    *,
    workspace: Path,
    state: RunState,
    run_path: Path,
    allow_write: bool,
    allow_scripts: bool,
    allow_shell: bool,
) -> str:
    ws = workspace.resolve()
    label = effective_workspace_label(workspace=ws, state=state)
    perms = []
    perms.append("write" if allow_write else "read-only")
    if allow_scripts:
        perms.append("scripts")
    if allow_shell:
        perms.append("shell")
    perms_text = ", ".join(perms)

    lines = [
        f"workspace: {ws}",
        f"workspace_label: {label}",
        f"run_state: {run_path}",
        f"active_node: {(state.active_node_alias or state.active_node_id or '')}".rstrip(),
        f"pending_gate: {str(bool(state.pending_gate)).lower()}",
        f"next_action: {state.next_action or ''}".rstrip(),
        f"permissions: {perms_text}",
    ]
    return "\n".join(lines).strip()

