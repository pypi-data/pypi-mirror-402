from __future__ import annotations

import argparse
from datetime import datetime
import os
from pathlib import Path
import re
import sys
import uuid

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.shortcuts import print_formatted_text

from .agent import ChatAgent
from .config import (
    OPENAI_IMITATORS,
    default_memory_dir,
    default_workspace_dir,
    load_env,
    resolve_config,
)
from .context_slimmer import maybe_summarize
from .memory import MemoryStore
from .mcp_client import McpToolRegistry, load_mcp_servers
from .skills import build_skills_prompt, load_skills, render_skills_prompt
from .local_tools import LocalToolConfig, build_local_tools, fs_write, text_extract_fence
from .thread_index import load_index, save_index, set_title, upsert_thread
from .workspace_state import (
    RunState,
    effective_workspace_label,
    ensure_workspace_state_dirs,
    load_run_state,
    render_where,
    resolve_workspace_path,
    save_run_state,
    workspace_paths,
)
from .context_tree import (
    create_node,
    load_tree,
    node_alias,
    render_ls,
    resolve_ref,
    save_tree,
    set_status,
)


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = _PROJECT_ROOT.parent.parent


def _workspace_root() -> Path:
    # Prefer explicit env override; otherwise derive from `.voidchat` home.
    return Path(os.getenv("VOIDCHAT_WORKSPACE_DIR") or default_workspace_dir()).resolve()


def _exit_with_error(message: str, code: int) -> None:
    print(f"[voidchat] {message}", file=sys.stderr)
    raise SystemExit(code)


def _ansi_enabled() -> bool:
    try:
        return bool(sys.stdout.isatty())
    except Exception:
        return False


def _c(s: str, color: str) -> str:
    # Simple ANSI coloring (ASCII-friendly). Keep identical style to voidmirror.
    colors = {
        "dim": "2",
        "red": "31",
        "green": "32",
        "yellow": "33",
        "blue": "34",
        "magenta": "35",
        "cyan": "36",
        "bold": "1",
    }
    code = colors.get(color, "0")
    return f"\x1b[{code}m{s}\x1b[0m"


def _p(s: str = "") -> None:
    if _ansi_enabled():
        print_formatted_text(ANSI(s))
    else:
        print(re.sub(r"\x1b\[[0-9;]*m", "", s))


def _generate_thread_filename() -> str:
    stamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    suffix = uuid.uuid4().hex[:7]
    return f"{stamp}-{suffix}.jsonl"


def _normalize_thread_arg(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        raise ValueError("thread 名称不能为空")
    if os.path.sep in raw or (os.path.altsep and os.path.altsep in raw):
        raise ValueError("thread 名称不能包含路径分隔符")
    if ".." in raw:
        raise ValueError("thread 名称不能包含 '..'")
    return raw


def _resolve_memory_dir(args) -> str:
    return getattr(args, "memory_dir", None) or os.getenv("VOIDCHAT_MEMORY_DIR") or default_memory_dir()


def _iter_thread_files(memory_dir: str) -> list[str]:
    if not os.path.isdir(memory_dir):
        return []
    files = []
    for name in os.listdir(memory_dir):
        if name.endswith(".jsonl") and os.path.isfile(os.path.join(memory_dir, name)):
            files.append(name)
    files.sort(key=lambda n: os.path.getmtime(os.path.join(memory_dir, n)), reverse=True)
    return files


def _pick_latest_thread(memory_dir: str) -> str | None:
    files = _iter_thread_files(memory_dir)
    return files[0] if files else None


def _peek_first_user_message(path: str) -> str:
    try:
        import json

        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:  # noqa: BLE001
                    continue
                if obj.get("role") == "user":
                    content = str(obj.get("content", "")).strip()
                    return content
    except OSError:
        return ""
    return ""


def _cmd_threads(memory_dir: str, limit: int) -> None:
    files = _iter_thread_files(memory_dir)[: max(0, limit)]
    index = load_index(memory_dir).get("threads", {})
    print(f"threads ({memory_dir}):")
    if not files:
        print("  (none)")
        return
    for name in files:
        path = os.path.join(memory_dir, name)
        meta = index.get(name) if isinstance(index, dict) else None
        title = ""
        if isinstance(meta, dict):
            title = str(meta.get("title", "")).strip()
        if not title:
            title = _peek_first_user_message(path)
        title = title.replace("\n", " ").strip()
        if len(title) > 60:
            title = title[:57] + "..."
        print(f"  {name}  {title}")


def _cmd_show(memory_dir: str, thread: str, raw: bool) -> None:
    name = _normalize_thread_arg(thread)
    filename = name if name.endswith(".jsonl") else f"{name}.jsonl"
    path = os.path.join(memory_dir, filename)
    if not os.path.isfile(path):
        _exit_with_error(f"找不到 thread: {filename}", 2)
    if raw:
        with open(path, "r", encoding="utf-8") as handle:
            sys.stdout.write(handle.read())
        return
    memory = MemoryStore(memory_dir, filename)
    for msg in memory.load_messages():
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role and content is not None:
            print(f"{role}> {str(content).strip()}")


def _cmd_rename(memory_dir: str, old: str, new: str) -> None:
    old_name = _normalize_thread_arg(old)
    new_name = _normalize_thread_arg(new)
    old_file = old_name if old_name.endswith(".jsonl") else f"{old_name}.jsonl"
    new_file = new_name if new_name.endswith(".jsonl") else f"{new_name}.jsonl"
    old_path = os.path.join(memory_dir, old_file)
    new_path = os.path.join(memory_dir, new_file)
    if not os.path.isfile(old_path):
        _exit_with_error(f"找不到 thread: {old_file}", 2)
    if os.path.exists(new_path):
        _exit_with_error(f"目标已存在: {new_file}", 2)
    os.makedirs(memory_dir, exist_ok=True)
    os.rename(old_path, new_path)
    # keep title record, move metadata to new filename key
    data = load_index(memory_dir)
    threads = data.get("threads", {})
    if isinstance(threads, dict) and old_file in threads:
        threads[new_file] = threads.pop(old_file)
        save_index(memory_dir, data)
    print(f"[voidchat] renamed: {old_file} -> {new_file}")


def _cmd_skills(config, *, verbose: bool) -> None:
    groups = _load_skills_groups(config)
    print("skills:")
    if not groups:
        print("  (none)")
        return
    total = 0
    for priority, skills in groups:
        print(f"  priority {priority}:")
        for skill in skills:
            total += 1
            if verbose:
                print(f"    - {skill.name}: {skill.description} ({skill.source_path})")
            else:
                print(f"    - {skill.name}: {skill.description}")
    print(f"total: {total}")


def _load_mcp_registry(config_path: str) -> McpToolRegistry | None:
    servers = load_mcp_servers(config_path)
    if not servers:
        return None
    registry = McpToolRegistry(servers)
    registry.load_tools()
    return registry


def _load_skills_index_template(path: str | None) -> str | None:
    if not path:
        return None
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except OSError:
        return None


def _load_skills_groups(config) -> list[tuple[int, list]]:
    # Deduplicate by skill.name inside each priority group.
    groups: dict[int, dict[str, object]] = {}
    for priority, path in config.skills_groups:
        skills = load_skills([path])
        if not skills:
            continue
        bucket = groups.setdefault(priority, {})
        for skill in skills:
            bucket.setdefault(skill.name, skill)

    selected = list(dict.fromkeys((config.use_skills or []) + (config.require_skills or [])))
    if selected:
        missing: set[str] = set()
        filtered: dict[int, dict[str, object]] = {}
        for priority in sorted(groups.keys(), reverse=True):
            bucket = groups[priority]
            picked = {name: bucket[name] for name in selected if name in bucket}
            if picked:
                filtered[priority] = picked
        for name in selected:
            found = any(name in groups[p] for p in groups)
            if not found:
                missing.add(name)
        if missing:
            _exit_with_error(f"找不到指定 skills: {', '.join(sorted(missing))}", 2)
        groups = filtered

    result: list[tuple[int, list]] = []
    for priority in sorted(groups.keys(), reverse=True):
        skills_list = list(groups[priority].values())
        result.append((priority, skills_list))
    return result


def _build_agent(config, registry) -> ChatAgent:
    skills_groups = _load_skills_groups(config)
    template_text = _load_skills_index_template(config.skills_index)
    include_details = bool(config.use_skills or config.require_skills)
    skills_prompt = build_skills_prompt(skills_groups, template_text, include_details=include_details)
    if config.require_skills:
        required = " ".join(config.require_skills)
        skills_prompt = (
            f"【强制技能】{required}\n"
            "你必须遵循这些技能的指令完成任务；若存在冲突，以强制技能为准。\n\n"
            f"{skills_prompt}"
        ).strip()
    skills_by_name = {}
    for _, skills in skills_groups:
        for skill in skills:
            skills_by_name.setdefault(skill.name, skill)

    def _tool_skills_read(args: dict) -> str:
        name = str(args.get("name", "")).strip()
        if not name:
            return "Missing required field: name"
        skill = skills_by_name.get(name)
        if not skill:
            available = " ".join(sorted(skills_by_name.keys()))
            return f"Skill not found: {name}. Available: {available}"
        content = render_skills_prompt([skill]).strip()
        return (
            f"{content}\n\n"
            "[Instruction] You now have the full instructions for this skill.\n"
            "- Produce the final deliverable in THIS response (do not say 'one moment', do not defer work).\n"
            "- This interface is text-only: do not claim you created files (png/pdf/etc). If the user asks for SVG, output SVG markup in a ```svg``` block.\n"
            "- If the user asks you to save/write/modify a local file and the write tools are available, you MUST call voidchat_fs_write / voidchat_fs_replace_lines and only claim success after the tool returns ok.\n"
            "- If the user asks to save/write/modify a local file but write tools are unavailable, tell them to re-run with --allow-write (or set VOIDCHAT_ALLOW_WRITE=1).\n"
            "- Only use voidchat_text_extract_fence when the input text actually contains fenced code blocks.\n"
            "- Do NOT call voidchat_skills_read again unless you truly need a different skill."
        ).strip()

    tool_cfg = LocalToolConfig(
        fs_root=config.fs_root,
        repo_root=str(_REPO_ROOT),
        allow_write=config.allow_write,
        allow_scripts=getattr(config, "allow_scripts", False),
        allow_shell=config.allow_shell,
        shell_allowlist=config.shell_allowlist,
    )
    other_tools, other_schemas = build_local_tools(tool_cfg)

    local_tool_schemas = [
        {
            "type": "function",
            "function": {
                "name": "voidchat_skills_read",
                "description": "读取一个已加载的 skill 的完整正文指令（来自 SKILL.md）",
                "parameters": {
                    "type": "object",
                    "properties": {"name": {"type": "string", "description": "skill 名称，如 xlsx"}},
                    "required": ["name"],
                    "additionalProperties": False,
                },
            },
        }
    ] + other_schemas

    return ChatAgent(
        api_key=config.api_key,
        base_url=config.base_url,
        model=config.model,
        temperature=config.temperature,
        system_prompt=config.system_prompt,
        skills_prompt=skills_prompt,
        mcp_registry=registry,
        local_tools={"voidchat_skills_read": _tool_skills_read, **other_tools},
        local_tool_schemas=local_tool_schemas,
        debug=config.debug,
    )


def _maybe_slim_conversation(
    agent: ChatAgent, memory: MemoryStore, conversation: list[dict], config
) -> list[dict]:
    slimmed, did_summarize = maybe_summarize(
        agent,
        conversation,
        max_tokens=config.context_max_tokens,
        ratio=config.summary_ratio,
        keep_last=config.context_keep_last,
    )
    if did_summarize:
        memory.replace_messages(slimmed)
    return slimmed


def _mask_api_key(value: str) -> str:
    if not value:
        return "MISSING"
    raw = value.strip()
    length = len(raw)
    if length <= 8:
        return f"{'*' * length} (len={length})"
    return f"{raw[:4]}...{raw[-4:]} (len={length})"


def _mask_env_value(key: str, value: str) -> str:
    if key.endswith("_API_KEY"):
        return _mask_api_key(value)
    if key == "VOIDCHAT_SYSTEM_PROMPT":
        return f"set(len={len(value)})"
    return value


def _print_env_section() -> None:
    env_keys = [
        "VOIDCHAT_HOME",
        "VOIDCHAT_API_KEY",
        "VOIDCHAT_BASE_URL",
        "VOIDCHAT_MODEL",
        "VOIDCHAT_EMBEDDING_MODEL",
        "VOIDCHAT_SYSTEM_PROMPT",
        "VOIDCHAT_MCP_CONFIG",
        "VOIDCHAT_WORKSPACE_DIR",
        "VOIDCHAT_SKILLS_DIR",
        "VOIDCHAT_SKILLS_GROUPS",
        "VOIDCHAT_SKILLS_INDEX",
        "VOIDCHAT_SKILLS_PRIORITY",
        "VOIDCHAT_MEMORY_DIR",
        "VOIDCHAT_CONTEXT_MAX_TOKENS",
        "VOIDCHAT_SUMMARY_RATIO",
        "VOIDCHAT_CONTEXT_KEEP_LAST",
        "VOIDCHAT_DEBUG",
        "VOIDCHAT_USE_SKILLS",
        "VOIDCHAT_REQUIRE_SKILLS",
        "VOIDCHAT_FS_ROOT",
        "VOIDCHAT_ALLOW_WRITE",
        "VOIDCHAT_ALLOW_SCRIPTS",
        "VOIDCHAT_ALLOW_SHELL",
        "VOIDCHAT_SHELL_ALLOWLIST",
        "OPENAI_IMITATORS",
    ]
    for prefix in OPENAI_IMITATORS:
        env_keys.extend(
            [
                f"{prefix}_API_KEY",
                f"{prefix}_BASE_URL",
                f"{prefix}_COMPLETION_MODEL",
                f"{prefix}_EMBEDDING_MODEL",
            ]
        )
    env_keys.append("OPENAI_API_KEY")

    print("env (set):")
    printed = 0
    for key in env_keys:
        value = os.getenv(key)
        if not value:
            continue
        rendered = _mask_env_value(key, value.strip())
        print(f"  {key}: {rendered}")
        printed += 1
    if printed == 0:
        print("  (none)")


def _print_overrides_section(args) -> None:
    overrides: list[tuple[str, str]] = []
    if getattr(args, "api_key", None):
        overrides.append(("--api-key", _mask_api_key(args.api_key)))
    if getattr(args, "base_url", None):
        overrides.append(("--base-url", args.base_url))
    if getattr(args, "model", None):
        overrides.append(("--model", args.model))
    if getattr(args, "temperature", None) is not None:
        overrides.append(("--temperature", str(args.temperature)))
    if getattr(args, "mcp_config", None):
        overrides.append(("--mcp-config", args.mcp_config))
    if getattr(args, "workspace_dir", None):
        overrides.append(("--workspace-dir", args.workspace_dir))
    if getattr(args, "skills_dir", None):
        overrides.append(("--skills-dir", ", ".join(args.skills_dir)))
    if getattr(args, "skills_group", None):
        overrides.append(("--skills-group", ", ".join(args.skills_group)))
    if getattr(args, "skills_index", None):
        overrides.append(("--skills-index", args.skills_index))
    if getattr(args, "skills_priority", None) is not None:
        overrides.append(("--skills-priority", str(args.skills_priority)))
    if getattr(args, "memory_dir", None):
        overrides.append(("--memory-dir", args.memory_dir))
    if getattr(args, "system_prompt", None):
        overrides.append(("--system-prompt", f"set(len={len(args.system_prompt)})"))
    if getattr(args, "context_max_tokens", None) is not None:
        overrides.append(("--context-max-tokens", str(args.context_max_tokens)))
    if getattr(args, "summary_ratio", None) is not None:
        overrides.append(("--summary-ratio", str(args.summary_ratio)))
    if getattr(args, "context_keep_last", None) is not None:
        overrides.append(("--context-keep-last", str(args.context_keep_last)))
    if getattr(args, "debug", None) is not None:
        overrides.append(("--debug", "true"))
    if getattr(args, "use_skill", None):
        overrides.append(("--use-skill", ", ".join(args.use_skill)))
    if getattr(args, "require_skill", None):
        overrides.append(("--require-skill", ", ".join(args.require_skill)))
    if getattr(args, "fs_root", None):
        overrides.append(("--fs-root", args.fs_root))
    if getattr(args, "allow_write", None):
        overrides.append(("--allow-write", "true"))
    if getattr(args, "allow_shell", None):
        overrides.append(("--allow-shell", "true"))
    if getattr(args, "allow_scripts", None):
        overrides.append(("--allow-scripts", "true"))
    if getattr(args, "shell_allow", None):
        overrides.append(("--shell-allow", ", ".join(args.shell_allow)))
    if getattr(args, "resume", False):
        overrides.append(("--resume", "true"))
    if getattr(args, "thread", None):
        overrides.append(("--thread", args.thread))
    if getattr(args, "no_stream", False):
        overrides.append(("--no-stream", "true"))
    if getattr(args, "imitator", None):
        overrides.append(("--imitator", args.imitator))

    print("overrides (cli):")
    if not overrides:
        print("  (none)")
        return
    for key, value in overrides:
        print(f"  {key}: {value}")


def _print_effective_section(config, *, workspace_path: Path | None = None) -> None:
    print("effective:")
    print(f"  api_key: {_mask_api_key(config.api_key)}")
    print(f"  base_url: {config.base_url}")
    print(f"  model: {config.model}")
    print(f"  embedding_model: {config.embedding_model or ''}")
    print(f"  system_prompt: {'set' if config.system_prompt else 'default'}")
    print(f"  mcp_config: {config.mcp_config}")
    if workspace_path is not None:
        print(f"  workspace: {workspace_path}")
    print(f"  workspace_dir: {getattr(config, 'workspace_dir', '') or _workspace_root()}")
    print(f"  skills_index: {config.skills_index or ''}")
    print(f"  skills_priority: {config.skills_priority}")
    print("  skills_groups:")
    for priority, path in config.skills_groups:
        print(f"    - {priority}={path}")
    print(f"  memory_dir: {config.memory_dir}")
    print(f"  thread_id: {config.thread_id}")
    print(f"  stream: {config.stream}")
    print(f"  context_max_tokens: {config.context_max_tokens}")
    print(f"  summary_ratio: {config.summary_ratio}")
    print(f"  context_keep_last: {config.context_keep_last}")
    print(f"  debug: {config.debug}")
    print(f"  fs_root: {config.fs_root}")
    print(f"  allow_write: {config.allow_write}")
    print(f"  allow_scripts: {getattr(config, 'allow_scripts', False)}")
    print(f"  allow_shell: {config.allow_shell}")
    if config.shell_allowlist:
        print(f"  shell_allowlist: {' '.join(config.shell_allowlist)}")
    if config.use_skills:
        print(f"  use_skills: {' '.join(config.use_skills)}")
    if config.require_skills:
        print(f"  require_skills: {' '.join(config.require_skills)}")


def _print_config(config, args, *, workspace_path: Path | None = None) -> None:
    print("voidchat config (env-first):")
    _print_env_section()
    _print_overrides_section(args)
    _print_effective_section(config, workspace_path=workspace_path)


def _parse_save_fence(value: str) -> tuple[str, str]:
    raw = (value or "").strip()
    if not raw or ":" not in raw:
        raise ValueError("save-fence 格式应为 <lang>:<path>，例如 svg:out.svg")
    lang, path = raw.split(":", 1)
    lang = lang.strip().lower()
    path = path.strip()
    if not lang or not path:
        raise ValueError("save-fence 格式应为 <lang>:<path>，例如 svg:out.svg")
    return lang, path


def _save_fence_from_text(
    config,
    *,
    text: str,
    lang: str,
    path: str,
    overwrite: bool,
    index: int = 0,
) -> str:
    tool_cfg = LocalToolConfig(
        fs_root=config.fs_root,
        repo_root=str(_REPO_ROOT),
        allow_write=config.allow_write,
        allow_scripts=getattr(config, "allow_scripts", False),
        allow_shell=config.allow_shell,
        shell_allowlist=config.shell_allowlist,
    )
    extracted = text_extract_fence(tool_cfg, {"text": text, "lang": lang, "index": int(index)})
    if extracted.strip() == "no fenced code block found":
        return extracted
    return fs_write(
        tool_cfg,
        {"path": path, "content": extracted, "overwrite": bool(overwrite)},
    )


def _run_chat(
    config,
    prompt: str,
    *,
    workspace_path: Path,
    save_fence: list[str],
    save_overwrite: bool,
) -> None:
    if not config.api_key:
        _exit_with_error("缺少 API key（VOIDCHAT_API_KEY 或 OPENAI_API_KEY）", 2)

    # WP-01: ensure host state root exists under <workspace>/.voidchat
    ws_paths = workspace_paths(workspace_path)
    ensure_workspace_state_dirs(ws_paths)
    ws_state = load_run_state(ws_paths.run_path)
    save_run_state(ws_paths.run_path, ws_state)

    try:
        registry = _load_mcp_registry(config.mcp_config)
    except Exception as exc:  # noqa: BLE001
        # Do not hard-fail on MCP for core chat workflows; proceed without MCP.
        registry = None
        if getattr(config, "debug", False):
            print(f"[voidchat][debug] MCP 配置错误（已忽略，继续无 MCP）: {exc}", file=sys.stderr)

    agent = _build_agent(config, registry)
    memory = MemoryStore(config.memory_dir, config.thread_id)
    conversation = memory.load_messages()
    if config.debug:
        print(
            f"[voidchat][debug] thread_file={memory.path} history_messages={len(conversation)}",
            file=sys.stderr,
        )
    conversation = _maybe_slim_conversation(agent, memory, conversation, config)
    system_message = agent.build_system_message()

    user_message = {"role": "user", "content": prompt}
    messages = [system_message] + conversation + [user_message]

    if config.stream:
        if _ansi_enabled():
            sys.stdout.write(_c("assistant> ", "green"))
            sys.stdout.flush()
        else:
            print("assistant> ", end="", flush=True)

    try:
        assistant_message = agent.run(
            messages,
            stream=config.stream,
            output=lambda chunk: (sys.stdout.write(chunk), sys.stdout.flush()),
        )
    except Exception as exc:  # noqa: BLE001
        _exit_with_error(f"模型调用失败: {exc}", 3)

    if config.stream:
        print("")
    else:
        print(assistant_message.get("content", ""))

    # Optional: host-side save fenced block from assistant output
    if save_fence:
        content = str(assistant_message.get("content", "") or "")
        for spec in save_fence:
            try:
                lang, out_path = _parse_save_fence(spec)
            except ValueError as exc:
                _exit_with_error(str(exc), 2)
            result = _save_fence_from_text(
                config,
                text=content,
                lang=lang,
                path=out_path,
                overwrite=bool(save_overwrite),
            )
            print(f"[voidchat] save-fence {lang}:{out_path}: {result}", file=sys.stderr)

    messages.append({"role": "assistant", "content": assistant_message.get("content", "")})
    new_messages = messages[1 + len(conversation) :]
    memory.append_messages(new_messages)
    # update thread index (title/summary)
    filename = os.path.basename(memory.path)
    first_user = prompt if not conversation else None
    upsert_thread(
        config.memory_dir,
        filename,
        title=None,
        first_user=first_user,
        last_user=prompt,
        message_count=len(conversation) + len(new_messages),
    )


def _handle_repl_host_command(
    *,
    line: str,
    config,
    workspace_path: Path,
    state: RunState,
) -> tuple[bool, Path, RunState, str | None]:
    """Handle `/command` in REPL.

    Returns: (handled, new_workspace_path, new_state, output_text)
    """
    raw = (line or "").strip()
    if not raw.startswith("/"):
        return False, workspace_path, state, None

    cmdline = raw[1:].strip()
    if not cmdline:
        return True, workspace_path, state, "[voidchat] 用法: /where | /workspace <path> | /ls | /go #n | /close #n | /reopen #n | /new-plan <title> | /new-task <title>"

    parts = cmdline.split(maxsplit=1)
    cmd = parts[0].strip().lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    if cmd == "where":
        paths = workspace_paths(workspace_path)
        # best-effort refresh alias display
        try:
            tree = load_tree(paths.context_tree_path, root_title=effective_workspace_label(workspace=workspace_path, state=state))
            if state.active_node_id and not state.active_node_alias:
                state.active_node_alias = node_alias(tree, state.active_node_id)
        except Exception:
            pass
        text = render_where(
            workspace=workspace_path,
            state=state,
            run_path=paths.run_path,
            allow_write=bool(config.allow_write),
            allow_scripts=bool(getattr(config, "allow_scripts", False)),
            allow_shell=bool(config.allow_shell),
        )
        return True, workspace_path, state, text

    if cmd == "workspace":
        if not arg:
            return True, workspace_path, state, "[voidchat] 用法: /workspace <path>"
        new_ws = resolve_workspace_path(workspace=arg, cwd=Path.cwd())
        new_paths = workspace_paths(new_ws)
        ensure_workspace_state_dirs(new_paths)
        new_state = load_run_state(new_paths.run_path)
        # WP-03: ensure context tree exists
        tree = load_tree(new_paths.context_tree_path, root_title=effective_workspace_label(workspace=new_ws, state=new_state))
        save_tree(new_paths.context_tree_path, tree)
        save_run_state(new_paths.run_path, new_state)
        return True, new_ws, new_state, f"[voidchat] workspace -> {new_ws}"

    # WP-03: Context Tree commands
    paths = workspace_paths(workspace_path)
    tree = load_tree(paths.context_tree_path, root_title=effective_workspace_label(workspace=workspace_path, state=state))

    if cmd == "ls":
        return True, workspace_path, state, render_ls(tree)

    if cmd == "go":
        if not arg:
            return True, workspace_path, state, "[voidchat] 用法: /go #n"
        node_id = resolve_ref(tree, arg)
        if not node_id:
            return True, workspace_path, state, f"[voidchat] 找不到节点: {arg}"
        state.active_node_id = node_id
        state.active_node_alias = node_alias(tree, node_id)
        save_run_state(paths.run_path, state)
        return True, workspace_path, state, f"[voidchat] active -> {state.active_node_alias or node_id}"

    if cmd in {"close", "reopen"}:
        if not arg:
            return True, workspace_path, state, f"[voidchat] 用法: /{cmd} #n"
        node_id = resolve_ref(tree, arg)
        if not node_id:
            return True, workspace_path, state, f"[voidchat] 找不到节点: {arg}"
        set_status(tree, node_id, "closed" if cmd == "close" else "open")
        save_tree(paths.context_tree_path, tree)
        if cmd == "close" and state.active_node_id == node_id:
            state.active_node_id = None
            state.active_node_alias = None
            save_run_state(paths.run_path, state)
        return True, workspace_path, state, f"[voidchat] {cmd} -> {node_alias(tree, node_id) or node_id}"

    if cmd in {"new-plan", "new-task"}:
        if not arg:
            return True, workspace_path, state, f"[voidchat] 用法: /{cmd} <title>"
        parent_id = "root"
        if cmd == "new-task" and state.active_node_id:
            active = tree.nodes.get(state.active_node_id)
            if active and active.type == "plan":
                parent_id = active.id
            elif active and active.type == "task" and active.parent_id:
                parent_id = active.parent_id
        node = create_node(
            tree,
            node_type="plan" if cmd == "new-plan" else "task",
            title=arg,
            parent_id=parent_id,
        )
        save_tree(paths.context_tree_path, tree)
        state.active_node_id = node.id
        state.active_node_alias = node.alias
        save_run_state(paths.run_path, state)
        return True, workspace_path, state, f"[voidchat] created {node.alias} [{node.type}] {node.title}"

    return True, workspace_path, state, f"[voidchat] 未知命令: /{cmd}（支持: /where, /workspace, /ls, /go, /close, /reopen, /new-plan, /new-task）"


def _run_repl(config, *, workspace_path: Path) -> None:
    if not config.api_key:
        _exit_with_error("缺少 API key（VOIDCHAT_API_KEY 或 OPENAI_API_KEY）", 2)

    try:
        registry = _load_mcp_registry(config.mcp_config)
    except Exception as exc:  # noqa: BLE001
        registry = None
        if getattr(config, "debug", False):
            print(f"[voidchat][debug] MCP 配置错误（已忽略，继续无 MCP）: {exc}", file=sys.stderr)

    agent = _build_agent(config, registry)
    system_message = agent.build_system_message()
    session = PromptSession()

    thread_id = config.thread_id
    last_assistant: str = ""
    current_workspace = workspace_path
    current_paths = workspace_paths(current_workspace)
    current_state = load_run_state(current_paths.run_path)

    while True:
        memory = MemoryStore(config.memory_dir, thread_id)
        conversation = memory.load_messages()
        if config.debug:
            print(
                f"[voidchat][debug] thread_file={memory.path} history_messages={len(conversation)}",
                file=sys.stderr,
            )
        conversation = _maybe_slim_conversation(agent, memory, conversation, config)

        try:
            prompt = session.prompt("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("")
            return

        if not prompt:
            continue

        handled, current_workspace, current_state, out = _handle_repl_host_command(
            line=prompt,
            config=config,
            workspace_path=current_workspace,
            state=current_state,
        )
        if handled:
            if out:
                print(out)
            continue

        if prompt in {":exit", ":quit", ":q"}:
            return
        if prompt == ":new":
            thread_id = _generate_thread_filename()
            print(f"[voidchat] 已切换新线程: {thread_id}")
            continue
        if prompt.startswith(":thread "):
            thread_id = prompt.split(" ", 1)[1].strip() or thread_id
            print(f"[voidchat] 已切换线程: {thread_id}")
            continue
        if prompt.startswith(":save "):
            # Usage: :save <lang> <path> [--overwrite] [--index N]
            parts = prompt.split()
            if len(parts) < 3:
                print("[voidchat] 用法: :save <lang> <path> [--overwrite] [--index N]")
                continue
            lang = parts[1].strip().lower()
            out_path = parts[2].strip()
            overwrite = False
            index = 0
            i = 3
            while i < len(parts):
                token = parts[i].strip()
                if token == "--overwrite":
                    overwrite = True
                    i += 1
                    continue
                if token == "--index" and i + 1 < len(parts):
                    try:
                        index = int(parts[i + 1])
                    except ValueError:
                        index = 0
                    i += 2
                    continue
                i += 1
            if not last_assistant.strip():
                print("[voidchat] 当前没有可保存的 assistant 输出（请先让模型输出包含 ```lang``` 的代码块）")
                continue
            result = _save_fence_from_text(
                config,
                text=last_assistant,
                lang=lang,
                path=out_path,
                overwrite=overwrite,
                index=index,
            )
            print(f"[voidchat] saved {lang} -> {out_path}: {result}")
            continue

        user_message = {"role": "user", "content": prompt}
        messages = [system_message] + conversation + [user_message]

        if config.stream:
            if _ansi_enabled():
                sys.stdout.write(_c("assistant> ", "green"))
                sys.stdout.flush()
            else:
                print("assistant> ", end="", flush=True)

        try:
            assistant_message = agent.run(
                messages,
                stream=config.stream,
                output=lambda chunk: (sys.stdout.write(chunk), sys.stdout.flush()),
            )
        except Exception as exc:  # noqa: BLE001
            _exit_with_error(f"模型调用失败: {exc}", 3)

        if config.stream:
            print("")
        else:
            print(assistant_message.get("content", ""))
        last_assistant = str(assistant_message.get("content", "") or "")

        messages.append({"role": "assistant", "content": assistant_message.get("content", "")})
        new_messages = messages[1 + len(conversation) :]
        memory.append_messages(new_messages)
        filename = os.path.basename(memory.path)
        first_user = prompt if not conversation else None
        upsert_thread(
            config.memory_dir,
            filename,
            title=None,
            first_user=first_user,
            last_user=prompt,
            message_count=len(conversation) + len(new_messages),
        )


def _build_parser() -> argparse.ArgumentParser:
    # NOTE: common args are added to both root + subcommands.
    # Use SUPPRESS so subparser defaults don't overwrite values parsed before subcommand.
    common = argparse.ArgumentParser(add_help=False, argument_default=argparse.SUPPRESS)
    common.add_argument("--api-key", help="API key")
    common.add_argument("--base-url", help="OpenAI compatible base_url")
    common.add_argument("--model", help="Model name")
    common.add_argument("--temperature", type=float, help="Sampling temperature")
    common.add_argument(
        "--mcp-config",
        help="MCP config file path (default: ./.voidchat/mcp.json)",
    )
    common.add_argument(
        "--workspace-dir",
        help="Workspace directory for workflow artifacts (env: VOIDCHAT_WORKSPACE_DIR; default: <.voidchat>/workspace)",
    )
    common.add_argument(
        "--workspace",
        "--workspace-path",
        dest="workspace",
        help="Workspace path for REPL/CLI working mode (default: current working directory)",
    )
    common.add_argument(
        "--skills-dir",
        action="append",
        help="Skills directory (default: search for .claude/skills)",
    )
    common.add_argument(
        "--skills-index",
        help="Skills index file (default: search for AGENTS.md)",
    )
    common.add_argument(
        "--skills-group",
        action="append",
        help="Skills group mapping, e.g. 2=/path/to/skills",
    )
    common.add_argument(
        "--skills-priority",
        type=int,
        help="Skills priority (default: 1)",
    )
    common.add_argument(
        "--memory-dir", help="Memory storage directory (default: ./.voidchat/memory)"
    )
    common.add_argument("--system-prompt", help="System prompt override")
    common.add_argument(
        "--context-max-tokens", type=int, help="Context token threshold (default: 8000)"
    )
    common.add_argument(
        "--summary-ratio", type=float, help="Summary ratio (0-1, default: 0.5)"
    )
    common.add_argument(
        "--context-keep-last",
        type=int,
        help="Keep last N messages after summary (default: 6)",
    )
    common.add_argument("--thread", help="Thread name or jsonl filename (under memory dir)")
    common.add_argument(
        "--resume",
        action="store_true",
        help="Resume latest thread (otherwise start a new one)",
    )
    common.add_argument(
        "--threads",
        action="store_true",
        help="List recent threads (alias of `voidchat threads`)",
    )
    common.add_argument("--no-stream", action="store_true", help="Disable streaming output")
    common.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logs (also via VOIDCHAT_DEBUG=1)",
    )
    common.add_argument(
        "--use-skill",
        action="append",
        help="Only load specified skill(s) by name (repeatable)",
    )
    common.add_argument(
        "--require-skill",
        action="append",
        help="Require specified skill(s) and enforce in system prompt (repeatable)",
    )
    common.add_argument(
        "--imitator",
        help="Force provider prefix, e.g. QWEN/ZHIPU/DEEPSEEK/OPENAI/GOOGLE/ANTHROPIC",
    )
    common.add_argument(
        "--fs-root",
        help="Filesystem root for local tools (default: current directory or VOIDCHAT_FS_ROOT)",
    )
    common.add_argument(
        "--allow-write",
        action="store_true",
        help="Allow local file write tools (fs_write/fs_replace_lines)",
    )
    common.add_argument(
        "--allow-shell",
        action="store_true",
        help="Allow controlled local shell tool (voidchat_shell)",
    )
    common.add_argument(
        "--allow-scripts",
        action="store_true",
        help="Allow running registered scripts via voidchat_script_run",
    )
    common.add_argument(
        "--shell-allow",
        action="append",
        help="Allowed commands for voidchat_shell (repeatable, e.g. --shell-allow rg --shell-allow git)",
    )
    common.add_argument(
        "--save-fence",
        action="append",
        help="Save fenced code block from assistant output, format: <lang>:<path> (e.g. svg:out.svg)",
    )
    common.add_argument(
        "--save-overwrite",
        action="store_true",
        help="Overwrite when using --save-fence",
    )

    parser = argparse.ArgumentParser(
        prog="voidchat",
        parents=[common],
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="Init: voidchat init",
    )
    subparsers = parser.add_subparsers(dest="command")

    init_cmd = subparsers.add_parser("init", help="Init .voidchat config directory", parents=[common])
    init_cmd.add_argument(
        "--local",
        action="store_true",
        help="Force creating ./.voidchat even if an upper-level .voidchat exists",
    )
    init_cmd.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing template files (mcp.json/.env.example) if present",
    )
    init_cmd.add_argument(
        "--no-skills",
        action="store_true",
        help="Do not create/copy skills dir into .voidchat (skills can be provided externally)",
    )

    subparsers.add_parser("repl", help="Interactive REPL", parents=[common])

    chat = subparsers.add_parser("chat", help="Single prompt", parents=[common])
    chat.add_argument("prompt", help="User prompt")
    subparsers.add_parser("config", help="Print resolved config", parents=[common])
    skills = subparsers.add_parser("skills", help="List loaded skills", parents=[common])
    skills.add_argument("--verbose", action="store_true", help="Include skill source path")
    threads = subparsers.add_parser("threads", help="List threads", parents=[common])
    threads.add_argument("--limit", type=int, default=20, help="Max items to show (default: 20)")
    show = subparsers.add_parser("show", help="Show thread messages", parents=[common])
    show.add_argument("thread", help="Thread name or jsonl filename")
    show.add_argument("--raw", action="store_true", help="Print raw jsonl")
    rename = subparsers.add_parser("rename", help="Rename thread file", parents=[common])
    rename.add_argument("old", help="Old thread name or jsonl filename")
    rename.add_argument("new", help="New thread name or jsonl filename")
    title_cmd = subparsers.add_parser("title", help="Set thread title", parents=[common])
    title_cmd.add_argument("thread", help="Thread name or jsonl filename")
    title_cmd.add_argument("title", help="New title")

    # Host-mode CLI (explicitly replayable; equivalent to /command in REPL)
    subparsers.add_parser("where", help="Show current workspace mode state", parents=[common])
    subparsers.add_parser("ls", help="List open context tree nodes", parents=[common])
    go = subparsers.add_parser("go", help="Set active node by #alias", parents=[common])
    go.add_argument("ref", help="Node reference, e.g. #1")
    close = subparsers.add_parser("close", help="Close node by #alias", parents=[common])
    close.add_argument("ref", help="Node reference, e.g. #1")
    reopen = subparsers.add_parser("reopen", help="Reopen node by #alias", parents=[common])
    reopen.add_argument("ref", help="Node reference, e.g. #1")
    new_plan = subparsers.add_parser("new-plan", help="Create a new plan node", parents=[common])
    new_plan.add_argument("title", help="Plan title")
    new_task = subparsers.add_parser("new-task", help="Create a new task node", parents=[common])
    new_task.add_argument("title", help="Task title")

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    load_env()
    if getattr(args, "threads", False) and not getattr(args, "command", None):
        args.command = "threads"
    if not getattr(args, "command", None):
        args.command = "repl"

    memory_dir = _resolve_memory_dir(args)
    if args.command == "threads":
        _cmd_threads(memory_dir, getattr(args, "limit", 20))
        return
    if args.command == "init":
        from .init import init_voidchat

        init_voidchat(
            local=bool(getattr(args, "local", False)),
            overwrite=bool(getattr(args, "overwrite", False)),
            copy_skills=not bool(getattr(args, "no_skills", False)),
        )
        return
    if args.command == "show":
        _cmd_show(memory_dir, getattr(args, "thread", ""), getattr(args, "raw", False))
        return
    if args.command == "rename":
        _cmd_rename(memory_dir, getattr(args, "old", ""), getattr(args, "new", ""))
        return
    if args.command == "title":
        name = _normalize_thread_arg(getattr(args, "thread", ""))
        filename = name if name.endswith(".jsonl") else f"{name}.jsonl"
        set_title(memory_dir, filename, getattr(args, "title", ""))
        print(f"[voidchat] titled: {filename}")
        return

    # Thread selection: default new thread, unless --thread or --resume
    if args.command in {"config", "skills", "where", "ls", "go", "close", "reopen", "new-plan", "new-task"}:
        resolved_thread = (
            _normalize_thread_arg(getattr(args, "thread", ""))
            if getattr(args, "thread", None)
            else (_pick_latest_thread(memory_dir) if getattr(args, "resume", False) else "AUTO")
        )
    else:
        resolved_thread = _normalize_thread_arg(args.thread) if getattr(args, "thread", None) else ""
        if not resolved_thread:
            if getattr(args, "resume", False):
                resolved_thread = _pick_latest_thread(memory_dir) or _generate_thread_filename()
            else:
                resolved_thread = _generate_thread_filename()

    config = resolve_config(
        api_key=getattr(args, "api_key", None),
        base_url=getattr(args, "base_url", None),
        model=getattr(args, "model", None),
        temperature=getattr(args, "temperature", None),
        mcp_config=getattr(args, "mcp_config", None),
        workspace_dir=getattr(args, "workspace_dir", None),
        skills_dirs=getattr(args, "skills_dir", None),
        skills_index=getattr(args, "skills_index", None),
        skills_priority=getattr(args, "skills_priority", None),
        skills_groups=getattr(args, "skills_group", None),
        memory_dir=memory_dir,
        thread_id=resolved_thread,
        stream=not getattr(args, "no_stream", False),
        imitator=getattr(args, "imitator", None),
        system_prompt=getattr(args, "system_prompt", None),
        context_max_tokens=getattr(args, "context_max_tokens", None),
        summary_ratio=getattr(args, "summary_ratio", None),
        context_keep_last=getattr(args, "context_keep_last", None),
        debug=getattr(args, "debug", None),
        use_skills=getattr(args, "use_skill", None),
        require_skills=getattr(args, "require_skill", None),
        fs_root=getattr(args, "fs_root", None),
        allow_write=getattr(args, "allow_write", None),
        allow_scripts=getattr(args, "allow_scripts", None),
        allow_shell=getattr(args, "allow_shell", None),
        shell_allowlist=getattr(args, "shell_allow", None),
    )

    workspace_path = resolve_workspace_path(
        workspace=getattr(args, "workspace", None),
        cwd=Path.cwd(),
    )

    # Ensure workspace host state exists for host-mode commands and chat/repl.
    ws_paths = workspace_paths(workspace_path)
    ensure_workspace_state_dirs(ws_paths)
    ws_state = load_run_state(ws_paths.run_path)
    tree = load_tree(ws_paths.context_tree_path, root_title=effective_workspace_label(workspace=workspace_path, state=ws_state))
    save_tree(ws_paths.context_tree_path, tree)
    if ws_state.active_node_id and not ws_state.active_node_alias:
        ws_state.active_node_alias = node_alias(tree, ws_state.active_node_id)
        save_run_state(ws_paths.run_path, ws_state)

    if getattr(args, "imitator", None):
        print(
            f"[voidchat] using imitator={args.imitator.strip().upper()} base_url={config.base_url} model={config.model}",
            file=sys.stderr,
        )

    if args.command == "chat":
        _run_chat(
            config,
            args.prompt,
            workspace_path=workspace_path,
            save_fence=getattr(args, "save_fence", None) or [],
            save_overwrite=getattr(args, "save_overwrite", False),
        )
        return
    if args.command == "where":
        print(
            render_where(
                workspace=workspace_path,
                state=ws_state,
                run_path=ws_paths.run_path,
                allow_write=bool(config.allow_write),
                allow_scripts=bool(getattr(config, "allow_scripts", False)),
                allow_shell=bool(config.allow_shell),
            )
        )
        return
    if args.command == "ls":
        print(render_ls(tree))
        return
    if args.command in {"go", "close", "reopen"}:
        ref = getattr(args, "ref", "")
        node_id = resolve_ref(tree, ref)
        if not node_id:
            _exit_with_error(f"找不到节点: {ref}", 2)
        if args.command == "go":
            ws_state.active_node_id = node_id
            ws_state.active_node_alias = node_alias(tree, node_id)
            save_run_state(ws_paths.run_path, ws_state)
            print(f"[voidchat] active -> {ws_state.active_node_alias or node_id}")
            return
        set_status(tree, node_id, "closed" if args.command == "close" else "open")
        save_tree(ws_paths.context_tree_path, tree)
        if args.command == "close" and ws_state.active_node_id == node_id:
            ws_state.active_node_id = None
            ws_state.active_node_alias = None
            save_run_state(ws_paths.run_path, ws_state)
        print(f"[voidchat] {args.command} -> {node_alias(tree, node_id) or node_id}")
        return
    if args.command in {"new-plan", "new-task"}:
        title = getattr(args, "title", "")
        if not title:
            _exit_with_error("title 不能为空", 2)
        parent_id = "root"
        if args.command == "new-task" and ws_state.active_node_id:
            active = tree.nodes.get(ws_state.active_node_id)
            if active and active.type == "plan":
                parent_id = active.id
            elif active and active.type == "task" and active.parent_id:
                parent_id = active.parent_id
        node = create_node(
            tree,
            node_type="plan" if args.command == "new-plan" else "task",
            title=title,
            parent_id=parent_id,
        )
        save_tree(ws_paths.context_tree_path, tree)
        ws_state.active_node_id = node.id
        ws_state.active_node_alias = node.alias
        save_run_state(ws_paths.run_path, ws_state)
        print(f"[voidchat] created {node.alias} [{node.type}] {node.title}")
        return
    if args.command == "config":
        _print_config(config, args, workspace_path=workspace_path)
        return
    if args.command == "skills":
        _cmd_skills(config, verbose=getattr(args, "verbose", False))
        return
    if args.command == "repl":
        _run_repl(config, workspace_path=workspace_path)
        return

    parser.print_help()


if __name__ == "__main__":
    main()

