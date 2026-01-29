from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Iterable


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _normalize_message(message: dict) -> dict:
    data = dict(message)
    if "tool_calls" in data and isinstance(data["tool_calls"], list):
        normalized_calls = []
        for tool_call in data["tool_calls"]:
            if not isinstance(tool_call, dict):
                normalized_calls.append({"raw": str(tool_call)})
                continue
            normalized = {
                "id": tool_call.get("id"),
                "type": tool_call.get("type", "function"),
                "function": tool_call.get("function", {}),
            }
            normalized_calls.append(normalized)
        data["tool_calls"] = normalized_calls
    return data


@dataclass
class MemoryStore:
    memory_dir: str
    thread_id: str

    @property
    def path(self) -> str:
        name = self.thread_id.strip()
        if not name:
            name = "default"
        filename = name if name.endswith(".jsonl") else f"{name}.jsonl"
        return os.path.join(self.memory_dir, filename)

    def load_messages(self) -> list[dict]:
        if not os.path.exists(self.path):
            return []
        messages: list[dict] = []
        with open(self.path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    messages.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return messages

    def append_messages(self, messages: Iterable[dict]) -> None:
        _ensure_dir(self.memory_dir)
        with open(self.path, "a", encoding="utf-8") as handle:
            for message in messages:
                normalized = _normalize_message(message)
                handle.write(json.dumps(normalized, ensure_ascii=False))
                handle.write("\n")

    def replace_messages(self, messages: Iterable[dict]) -> None:
        _ensure_dir(self.memory_dir)
        with open(self.path, "w", encoding="utf-8") as handle:
            for message in messages:
                normalized = _normalize_message(message)
                handle.write(json.dumps(normalized, ensure_ascii=False))
                handle.write("\n")
