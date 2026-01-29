from __future__ import annotations

import json
import os
import sys
from typing import Any, Callable

from openai import OpenAI

from .mcp_client import McpToolRegistry


BASE_SYSTEM_PROMPT = """You are VoidChat, a practical assistant.

Tool policy (critical):
- Use tools when they are needed to complete the user's request.
- Never claim you saved/modified files unless you actually called the relevant file tool and it succeeded.
  - If the user asks to save/modify a file but write tools are unavailable, explicitly tell them to re-run with write permission enabled (e.g. --allow-write / VOIDCHAT_ALLOW_WRITE=1).
- Never claim you executed shell commands unless you actually called the shell tool and it succeeded.

If a tool call fails, explain the error and continue (or ask for the required permission/flags).
Keep responses concise unless asked otherwise.
"""


def _parse_tool_args(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Some OpenAI-compatible providers may return non-strict JSON with extra trailing text.
        # Best-effort: extract the first balanced JSON object from the string.
        text = str(raw)
        start = text.find("{")
        if start != -1:
            depth = 0
            for i in range(start, len(text)):
                ch = text[i]
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        candidate = text[start : i + 1]
                        try:
                            return json.loads(candidate)
                        except json.JSONDecodeError:
                            break
        return {"_raw": raw}


def _tool_calls_from_message(message: Any) -> list[dict[str, Any]]:
    tool_calls = []
    for idx, tool_call in enumerate(message.tool_calls or []):
        call_id = tool_call.id or f"call_{idx}"
        tool_calls.append(
            {
                "id": call_id,
                "type": "function",
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments,
                },
            }
        )
    return tool_calls


class ChatAgent:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        temperature: float,
        system_prompt: str | None,
        skills_prompt: str,
        mcp_registry: McpToolRegistry | None,
        local_tools: dict[str, Callable[[dict[str, Any]], str]] | None = None,
        local_tool_schemas: list[dict[str, Any]] | None = None,
        debug: bool = False,
    ) -> None:
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._base_url = base_url
        self._model = model
        self._temperature = temperature
        self._system_prompt = system_prompt.strip() if system_prompt else ""
        self._skills_prompt = skills_prompt
        self._mcp_registry = mcp_registry
        self._local_tools = local_tools or {}
        self._local_tool_schemas = local_tool_schemas or []
        self._debug = debug

    def _debug_log(self, message: str) -> None:
        if not self._debug:
            return
        print(f"[voidchat][debug] {message}", file=sys.stderr)

    def build_system_message(self) -> dict[str, str]:
        prompt = self._system_prompt or BASE_SYSTEM_PROMPT
        if self._skills_prompt:
            prompt = f"{prompt}\n\n{self._skills_prompt}"
        return {"role": "system", "content": prompt.strip()}

    def summarize_messages(self, messages: list[dict[str, Any]], max_tokens: int) -> str:
        summary_prompt = (
            "You are a summarization assistant. Summarize the conversation so that "
            "future turns can continue seamlessly. Preserve user intent, preferences, "
            "decisions, and open questions. Keep it concise."
        )
        transcript = _render_messages_for_summary(messages)
        self._debug_log(
            f"summarize request base_url={self._base_url} model={self._model} max_tokens={max_tokens}"
        )
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": summary_prompt},
                {"role": "user", "content": transcript},
            ],
            temperature=0.1,
            max_tokens=max_tokens,
        )
        self._debug_log(
            f"summarize response model={getattr(response, 'model', None)}"
        )
        return (response.choices[0].message.content or "").strip()

    def run(
        self,
        messages: list[dict[str, Any]],
        *,
        stream: bool,
        output: Callable[[str], None],
    ) -> dict[str, Any]:
        disabled_tool_names: set[str] = set()
        skill_read_used = False

        def _build_tools() -> list[dict[str, Any]]:
            tools: list[dict[str, Any]] = []
            if self._local_tool_schemas:
                for schema in self._local_tool_schemas:
                    name = None
                    if isinstance(schema, dict):
                        fn = schema.get("function")
                        if isinstance(fn, dict):
                            name = fn.get("name")
                    if name and name in disabled_tool_names:
                        continue
                    tools.append(schema)
            if self._mcp_registry and self._mcp_registry.tools:
                tools.extend(self._mcp_registry.to_openai_tools())
            return tools

        tool_rounds = 0
        max_tool_rounds = 8
        while True:
            tools = _build_tools()
            if stream:
                content, tool_calls, finish_reason = self._stream_chat(messages, tools, output)
            else:
                content, tool_calls, finish_reason = self._non_stream_chat(messages, tools)

            if tool_calls:
                tool_rounds += 1
                if tool_rounds > max_tool_rounds:
                    self._debug_log("tool call loop detected; aborting")
                    return {
                        "role": "assistant",
                        "content": "Tool call loop detected; aborting to avoid infinite loop.",
                        "finish_reason": "tool_loop",
                    }
                messages.append({"role": "assistant", "tool_calls": tool_calls})
                tool_messages = []
                for tool_call in tool_calls:
                    tool_name = tool_call["function"]["name"]
                    tool_args = _parse_tool_args(tool_call["function"].get("arguments"))
                    try:
                        if tool_name in self._local_tools:
                            self._debug_log(f"local tool call: {tool_name} args={tool_args}")
                            result = self._local_tools[tool_name](tool_args)
                        elif self._mcp_registry:
                            self._debug_log(f"mcp tool call: {tool_name} args={tool_args}")
                            result = self._mcp_registry.call_tool(tool_name, tool_args)
                        else:
                            result = f"Tool not available: {tool_name}"
                    except Exception as exc:  # noqa: BLE001
                        result = f"Tool error: {exc}"
                    if self._debug:
                        preview = result.replace("\n", "\\n")
                        self._debug_log(f"tool result: {tool_name} len={len(result)} preview={preview[:200]}")
                    # Avoid "skill browsing" loops: allow at most one skills_read per run.
                    if tool_name == "voidchat_skills_read":
                        if skill_read_used:
                            disabled_tool_names.add("voidchat_skills_read")
                            result = (
                                "Skill already provided. Do NOT call voidchat_skills_read again. "
                                "Proceed to answer the user now."
                            )
                        else:
                            skill_read_used = True
                            disabled_tool_names.add("voidchat_skills_read")
                    tool_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": result,
                        }
                    )
                messages.extend(tool_messages)
                continue

            return {"role": "assistant", "content": content, "finish_reason": finish_reason}

    def _non_stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> tuple[str, list[dict[str, Any]], str | None]:
        self._debug_log(
            f"chat request base_url={self._base_url} model={self._model} stream=false tools={len(tools)} messages={len(messages)}"
        )
        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            tools=tools or None,
            tool_choice="auto" if tools else None,
            temperature=self._temperature,
        )
        choice = response.choices[0]
        tool_calls = _tool_calls_from_message(choice.message)
        usage = getattr(response, "usage", None)
        usage_text = ""
        if usage is not None:
            usage_text = (
                f" usage(prompt={getattr(usage,'prompt_tokens',None)} completion={getattr(usage,'completion_tokens',None)} total={getattr(usage,'total_tokens',None)})"
            )
        self._debug_log(
            f"chat response model={getattr(response, 'model', None)} finish_reason={choice.finish_reason} tool_calls={len(tool_calls)}{usage_text}"
        )
        return choice.message.content or "", tool_calls, choice.finish_reason

    def _stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        output: Callable[[str], None],
    ) -> tuple[str, list[dict[str, Any]], str | None]:
        tool_calls_acc: list[dict[str, Any]] = []
        content_parts: list[str] = []
        finish_reason = None
        response_model = None

        self._debug_log(
            f"chat request base_url={self._base_url} model={self._model} stream=true tools={len(tools)} messages={len(messages)}"
        )
        stream = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            tools=tools or None,
            tool_choice="auto" if tools else None,
            temperature=self._temperature,
            stream=True,
        )
        for chunk in stream:
            if response_model is None:
                response_model = getattr(chunk, "model", None)
            choice = chunk.choices[0]
            finish_reason = choice.finish_reason or finish_reason
            delta = choice.delta
            # Optional: some OpenAI-compatible providers stream reasoning in a separate field.
            # Enable with VOIDCHAT_STREAM_REASONING=1.
            reasoning = getattr(delta, "reasoning", None) or getattr(delta, "reasoning_content", None)
            if reasoning and (os.getenv("VOIDCHAT_STREAM_REASONING") or "").strip().lower() in {"1", "true", "yes"}:
                output(str(reasoning))
            if delta.content:
                output(delta.content)
                content_parts.append(delta.content)
            if delta.tool_calls:
                for tool_call in delta.tool_calls:
                    index = tool_call.index or 0
                    while len(tool_calls_acc) <= index:
                        tool_calls_acc.append(
                            {
                                "id": None,
                                "type": "function",
                                "function": {"name": None, "arguments": ""},
                            }
                        )
                    entry = tool_calls_acc[index]
                    if tool_call.id:
                        entry["id"] = tool_call.id
                    if tool_call.function:
                        if tool_call.function.name:
                            entry["function"]["name"] = tool_call.function.name
                        if tool_call.function.arguments:
                            entry["function"]["arguments"] += tool_call.function.arguments

        tool_calls = []
        for idx, call in enumerate(tool_calls_acc):
            if not call["function"]["name"]:
                continue
            call_id = call["id"] or f"call_{idx}"
            tool_calls.append(
                {
                    "id": call_id,
                    "type": "function",
                    "function": {
                        "name": call["function"]["name"],
                        "arguments": call["function"]["arguments"],
                    },
                }
            )
        self._debug_log(
            f"chat response model={response_model} finish_reason={finish_reason} tool_calls={len(tool_calls)}"
        )
        return "".join(content_parts), tool_calls, finish_reason


def _render_messages_for_summary(messages: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for message in messages:
        role = message.get("role", "unknown")
        content = message.get("content", "")
        if isinstance(content, list):
            content = " ".join(str(item) for item in content)
        if role == "tool":
            tool_id = message.get("tool_call_id", "")
            parts.append(f"[tool:{tool_id}] {content}")
        else:
            parts.append(f"[{role}] {content}")
    return "\n".join(parts).strip()
