from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Literal
import uuid


NodeType = Literal["root", "plan", "task"]
NodeStatus = Literal["open", "closed"]


@dataclass
class ContextNode:
    id: str
    alias: str
    type: NodeType
    parent_id: str | None
    status: NodeStatus
    title: str

    # Forward-compatible fields (not required for WP-03 runtime)
    summary: str | None = None
    pinned_facts: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    thread_ref: str | None = None
    policy: dict[str, Any] | None = None


@dataclass
class ContextTree:
    schema_version: int
    nodes: dict[str, ContextNode]
    alias_to_id: dict[str, str]
    next_alias: int


def _root_node(*, title: str) -> ContextNode:
    return ContextNode(
        id="root",
        alias="#0",
        type="root",
        parent_id=None,
        status="open",
        title=title,
    )


def _new_id() -> str:
    return uuid.uuid4().hex


def _parse_node(obj: dict[str, Any]) -> ContextNode | None:
    try:
        node_id = str(obj.get("id") or "").strip()
        alias = str(obj.get("alias") or "").strip()
        node_type = str(obj.get("type") or "").strip()
        parent_id = obj.get("parent_id")
        status = str(obj.get("status") or "").strip()
        title = str(obj.get("title") or "").strip()
        if parent_id is not None:
            parent_id = str(parent_id).strip()
        if not node_id or not alias or node_type not in {"root", "plan", "task"}:
            return None
        if status not in {"open", "closed"}:
            status = "open"
        return ContextNode(
            id=node_id,
            alias=alias,
            type=node_type,  # type: ignore[assignment]
            parent_id=parent_id or None,
            status=status,  # type: ignore[assignment]
            title=title,
            summary=(str(obj.get("summary")).strip() if obj.get("summary") else None),
            pinned_facts=list(obj.get("pinned_facts") or []),
            artifacts=list(obj.get("artifacts") or []),
            thread_ref=(str(obj.get("thread_ref")).strip() if obj.get("thread_ref") else None),
            policy=(obj.get("policy") if isinstance(obj.get("policy"), dict) else None),
        )
    except Exception:
        return None


def new_tree(*, root_title: str) -> ContextTree:
    root = _root_node(title=root_title)
    return ContextTree(
        schema_version=1,
        nodes={root.id: root},
        alias_to_id={root.alias: root.id},
        next_alias=1,
    )


def load_tree(path: Path, *, root_title: str) -> ContextTree:
    try:
        if not path.is_file():
            return new_tree(root_title=root_title)
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return new_tree(root_title=root_title)

    if not isinstance(data, dict):
        return new_tree(root_title=root_title)

    schema_version = int(data.get("schema_version") or 1)
    nodes_raw = data.get("nodes")
    nodes: dict[str, ContextNode] = {}
    alias_to_id: dict[str, str] = {}

    if isinstance(nodes_raw, list):
        for item in nodes_raw:
            if not isinstance(item, dict):
                continue
            node = _parse_node(item)
            if not node:
                continue
            nodes[node.id] = node
            alias_to_id[node.alias] = node.id
    elif isinstance(nodes_raw, dict):
        for _, item in nodes_raw.items():
            if not isinstance(item, dict):
                continue
            node = _parse_node(item)
            if not node:
                continue
            nodes[node.id] = node
            alias_to_id[node.alias] = node.id

    next_alias = int(data.get("next_alias") or 1)
    if "root" not in nodes:
        root = _root_node(title=root_title)
        nodes[root.id] = root
        alias_to_id.setdefault(root.alias, root.id)

    # Ensure root title follows current workspace label (best effort).
    try:
        nodes["root"].title = root_title  # type: ignore[misc]
    except Exception:
        pass

    # Ensure alias counter is ahead of existing aliases.
    max_seen = 0
    for alias in alias_to_id.keys():
        if alias.startswith("#") and alias[1:].isdigit():
            max_seen = max(max_seen, int(alias[1:]))
    next_alias = max(next_alias, max_seen + 1)

    return ContextTree(
        schema_version=schema_version,
        nodes=nodes,
        alias_to_id=alias_to_id,
        next_alias=next_alias,
    )


def save_tree(path: Path, tree: ContextTree) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    nodes_list = []
    for node in tree.nodes.values():
        nodes_list.append(asdict(node))

    payload = {
        "schema_version": int(tree.schema_version or 1),
        "next_alias": int(tree.next_alias or 1),
        "nodes": nodes_list,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        delete=False,
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
    ) as handle:
        tmp_path = Path(handle.name)
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    tmp_path.replace(path)


def resolve_ref(tree: ContextTree, ref: str) -> str | None:
    raw = (ref or "").strip()
    if not raw:
        return None
    if raw in tree.nodes:
        return raw
    if raw in tree.alias_to_id:
        return tree.alias_to_id[raw]
    # accept "1" as shorthand for "#1"
    if raw.isdigit():
        return tree.alias_to_id.get(f"#{raw}")
    return None


def node_alias(tree: ContextTree, node_id: str) -> str | None:
    node = tree.nodes.get(node_id)
    return node.alias if node else None


def create_node(
    tree: ContextTree,
    *,
    node_type: NodeType,
    title: str,
    parent_id: str,
) -> ContextNode:
    node_id = _new_id()
    alias = f"#{int(tree.next_alias)}"
    tree.next_alias = int(tree.next_alias) + 1

    node = ContextNode(
        id=node_id,
        alias=alias,
        type=node_type,
        parent_id=parent_id,
        status="open",
        title=title.strip(),
    )
    tree.nodes[node.id] = node
    tree.alias_to_id[alias] = node.id
    return node


def set_status(tree: ContextTree, node_id: str, status: NodeStatus) -> None:
    node = tree.nodes.get(node_id)
    if not node:
        return
    if node.type == "root":
        node.status = "open"
        return
    node.status = status


def open_children(tree: ContextTree, parent_id: str) -> list[ContextNode]:
    children = [n for n in tree.nodes.values() if n.parent_id == parent_id and n.status == "open"]
    # Stable-ish order by alias number.
    def _key(n: ContextNode) -> int:
        if n.alias.startswith("#") and n.alias[1:].isdigit():
            return int(n.alias[1:])
        return 10**9

    return sorted(children, key=_key)


def render_ls(tree: ContextTree) -> str:
    lines: list[str] = []
    lines.append("open nodes:")

    def walk(parent_id: str, indent: int) -> None:
        for child in open_children(tree, parent_id):
            lines.append(f"{'  ' * indent}- {child.alias} [{child.type}] {child.title}".rstrip())
            walk(child.id, indent + 1)

    walk("root", 0)
    if len(lines) == 1:
        lines.append("  (none)")
    return "\n".join(lines)

