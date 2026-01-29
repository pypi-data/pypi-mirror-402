from __future__ import annotations

from typing import Any

from .agent import ChatAgent


def estimate_tokens(messages: list[dict[str, Any]]) -> int:
    total_chars = 0
    for message in messages:
        content = message.get("content", "")
        if isinstance(content, list):
            content = " ".join(str(item) for item in content)
        total_chars += len(str(content))
    # rough heuristic: 1 token ~= 4 chars
    return max(1, total_chars // 4)


def maybe_summarize(
    agent: ChatAgent,
    messages: list[dict[str, Any]],
    *,
    max_tokens: int,
    ratio: float,
    keep_last: int,
) -> tuple[list[dict[str, Any]], bool]:
    if max_tokens <= 0:
        return messages, False
    current_tokens = estimate_tokens(messages)
    if current_tokens <= max_tokens:
        return messages, False

    target_tokens = max(32, int(max_tokens * ratio))
    summary = agent.summarize_messages(messages, max_tokens=target_tokens)
    tail = messages[-keep_last:] if keep_last > 0 else []
    if not summary:
        # fallback: keep the latest few messages
        trimmed = tail or (messages[-6:] if len(messages) > 6 else messages)
        return trimmed, True
    return [{"role": "assistant", "content": f"[summary]\n{summary}"}] + tail, True
