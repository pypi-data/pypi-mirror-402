from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime


INDEX_FILENAME = "threads.json"


@dataclass(frozen=True)
class ThreadMeta:
    filename: str
    title: str
    created_at: str
    updated_at: str
    first_user: str | None = None
    last_user: str | None = None
    message_count: int | None = None


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _index_path(memory_dir: str) -> str:
    return os.path.join(memory_dir, INDEX_FILENAME)


def load_index(memory_dir: str) -> dict:
    path = _index_path(memory_dir)
    if not os.path.isfile(path):
        return {"threads": {}}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
            if not isinstance(data, dict):
                return {"threads": {}}
            if "threads" not in data or not isinstance(data["threads"], dict):
                return {"threads": {}}
            return data
    except Exception:  # noqa: BLE001
        return {"threads": {}}


def save_index(memory_dir: str, data: dict) -> None:
    os.makedirs(memory_dir, exist_ok=True)
    path = _index_path(memory_dir)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def upsert_thread(
    memory_dir: str,
    filename: str,
    *,
    title: str | None = None,
    first_user: str | None = None,
    last_user: str | None = None,
    message_count: int | None = None,
) -> None:
    data = load_index(memory_dir)
    threads = data.setdefault("threads", {})
    now = _now_iso()
    existing = threads.get(filename)
    if not isinstance(existing, dict):
        existing = {"created_at": now}

    existing["updated_at"] = now
    existing.setdefault("created_at", now)
    existing.setdefault("title", "")

    if title is not None:
        existing["title"] = title
    if first_user is not None and first_user.strip():
        existing.setdefault("first_user", first_user.strip())
        # If title is empty, default to first user prompt
        if not str(existing.get("title", "")).strip():
            existing["title"] = first_user.strip()
    if last_user is not None and last_user.strip():
        existing["last_user"] = last_user.strip()
    if message_count is not None:
        existing["message_count"] = int(message_count)

    threads[filename] = existing
    save_index(memory_dir, data)


def set_title(memory_dir: str, filename: str, title: str) -> None:
    upsert_thread(memory_dir, filename, title=title)

