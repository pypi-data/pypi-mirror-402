from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Iterable
import re

from dotenv import load_dotenv


DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-5-mini"
DEFAULT_VOIDCHAT_DIR = ".voidchat"
DEFAULT_MEMORY_DIR = "./.voidchat/memory"  # legacy string default (prefer computed default via _default_voidchat_home)
DEFAULT_MCP_CONFIG = "./.voidchat/mcp.json"  # legacy string default (prefer computed default via _default_voidchat_home)
DEFAULT_WORKSPACE_DIR = "./.voidchat/workspace"
DEFAULT_CLAUDE_SKILLS_DIR = ".claude/skills"
DEFAULT_SKILLS_INDEX = "AGENTS.md"
DEFAULT_CONTEXT_MAX_TOKENS = 8000
DEFAULT_SUMMARY_RATIO = 0.5
DEFAULT_CONTEXT_KEEP_LAST = 6
DEFAULT_SKILLS_PRIORITY = 1
DEFAULT_SYSTEM_PROMPT = ""
DEFAULT_DEBUG = False
DEFAULT_FS_ROOT = "."
DEFAULT_ALLOW_WRITE = False
DEFAULT_ALLOW_SCRIPTS = False
DEFAULT_ALLOW_SHELL = False
DEFAULT_SHELL_ALLOWLIST: list[str] = []
OPENAI_IMITATORS = ["OPENAI", "QWEN", "DEEPSEEK", "ZHIPU"]


def _split_paths(value: str | None) -> list[str]:
    if not value:
        return []
    raw = value.replace(os.pathsep, ",")
    parts = [p.strip() for p in re.split(r"[,\s]+", raw) if p.strip()]
    return parts


def _split_list(value: str | None) -> list[str]:
    if not value:
        return []
    raw = value.strip()
    if not raw:
        return []
    return [p.strip() for p in re.split(r"[,\s]+", raw) if p.strip()]


def _find_claude_skills_dir(start: str) -> str | None:
    current = os.path.abspath(start)
    while True:
        candidate = os.path.join(current, DEFAULT_CLAUDE_SKILLS_DIR)
        if os.path.isdir(candidate):
            return candidate
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


def _find_skills_index_upwards(start: str) -> str | None:
    current = os.path.abspath(start)
    while True:
        candidate = os.path.join(current, DEFAULT_SKILLS_INDEX)
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


@dataclass(frozen=True)
class AppConfig:
    api_key: str
    base_url: str
    model: str
    embedding_model: str | None
    system_prompt: str
    temperature: float
    mcp_config: str
    workspace_dir: str
    skills_index: str | None
    skills_priority: int
    skills_dirs: list[str]
    skills_groups: list[tuple[int, str]]
    memory_dir: str
    thread_id: str
    stream: bool
    context_max_tokens: int
    summary_ratio: float
    context_keep_last: int
    debug: bool
    use_skills: list[str]
    require_skills: list[str]
    fs_root: str
    allow_write: bool
    allow_scripts: bool
    allow_shell: bool
    shell_allowlist: list[str]


def _find_dotenv_upwards(start: str) -> str | None:
    current = os.path.abspath(start)
    while True:
        candidate = os.path.join(current, ".env")
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


def _load_dotenv() -> None:
    path = _find_dotenv_upwards(os.getcwd())
    if path:
        load_dotenv(path, override=False)


def load_env() -> None:
    """Load .env from current directory upwards (non-overriding)."""
    _load_dotenv()


def _find_voidchat_home_upwards(start: str) -> str | None:
    """Find a `.voidchat/` directory from start upwards.

    This enables running `voidchat` from any subdirectory of a project while
    still using the same `.voidchat` config/memory/workspace roots.
    """
    current = os.path.abspath(start)
    while True:
        candidate = os.path.join(current, DEFAULT_VOIDCHAT_DIR)
        if os.path.isdir(candidate):
            return candidate
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


def _default_voidchat_home() -> str:
    """Resolve effective `.voidchat` home directory (absolute).

    Precedence:
    - VOIDCHAT_HOME (explicit absolute/relative path)
    - Search upwards from cwd for `.voidchat/`
    - Fallback to `./.voidchat` (under cwd)
    """
    env_home = (os.getenv("VOIDCHAT_HOME") or "").strip()
    if env_home:
        return os.path.abspath(env_home)
    found = _find_voidchat_home_upwards(os.getcwd())
    if found:
        return os.path.abspath(found)
    return os.path.abspath(os.path.join(os.getcwd(), DEFAULT_VOIDCHAT_DIR))


def default_memory_dir() -> str:
    """Default memory dir when VOIDCHAT_MEMORY_DIR is not set."""
    return os.path.join(_default_voidchat_home(), "memory")


def default_mcp_config() -> str:
    """Default mcp.json path when VOIDCHAT_MCP_CONFIG is not set."""
    return os.path.join(_default_voidchat_home(), "mcp.json")


def default_workspace_dir() -> str:
    """Default workspace dir when VOIDCHAT_WORKSPACE_DIR is not set."""
    return os.path.join(_default_voidchat_home(), "workspace")


def default_skills_dir() -> str:
    """Default `.voidchat/skills` dir path (may not exist)."""
    return os.path.join(_default_voidchat_home(), "skills")


def _parse_imitators(value: str | None) -> tuple[int | None, list[str] | None]:
    if not value:
        return None, None
    raw = value.strip()
    if not raw:
        return None, None
    if raw.isdigit():
        return int(raw), None
    parts = [part.strip().upper() for part in re.split(r"[,\s]+", raw) if part.strip()]
    return None, parts or None


def _parse_skills_groups(items: Iterable[str], default_priority: int) -> list[tuple[int, str]]:
    groups: list[tuple[int, str]] = []
    for item in items:
        raw = item.strip()
        if not raw:
            continue
        priority = default_priority
        path = raw
        if "=" in raw:
            left, right = raw.split("=", 1)
            if left.strip().isdigit():
                priority = int(left.strip())
                path = right.strip()
        elif ":" in raw:
            left, right = raw.split(":", 1)
            if left.strip().isdigit():
                priority = int(left.strip())
                path = right.strip()
        if path:
            groups.append((priority, path))
    return groups


def _parse_int(value: str | None, default: int) -> int:
    if not value:
        return default
    raw = value.strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _parse_ratio(value: str | None, default: float) -> float:
    if not value:
        return default
    raw = value.strip()
    if not raw:
        return default
    try:
        ratio = float(raw)
    except ValueError:
        return default
    if ratio <= 0 or ratio >= 1:
        return default
    return ratio


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    raw = value.strip().lower()
    if not raw:
        return default
    if raw in {"1", "true", "yes", "y", "on"}:
        return True
    if raw in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _provider_env(prefix: str) -> dict | None:
    api_key = (os.getenv(f"{prefix}_API_KEY") or "").strip()
    if not api_key:
        return None
    base_url = (os.getenv(f"{prefix}_BASE_URL") or "").strip() or None
    completion_model = _normalize_model_value(os.getenv(f"{prefix}_COMPLETION_MODEL"))
    embedding_model = _normalize_model_value(os.getenv(f"{prefix}_EMBEDDING_MODEL"))
    if not base_url and prefix == "OPENAI":
        base_url = DEFAULT_BASE_URL
    if not base_url:
        return None
    return {
        "name": prefix,
        "api_key": api_key,
        "base_url": base_url,
        "completion_model": completion_model,
        "embedding_model": embedding_model,
    }


def _resolve_provider_settings() -> dict | None:
    imitators, preferred = _parse_imitators(os.getenv("OPENAI_IMITATORS"))
    if imitators is None and not preferred:
        return None

    # Only used when OPENAI_IMITATORS is set.
    prefixes = preferred or OPENAI_IMITATORS
    providers: list[dict] = []
    for prefix in prefixes:
        cfg = _provider_env(prefix)
        if cfg:
            providers.append(cfg)
    if not providers:
        return None
    if imitators and imitators < len(providers):
        providers = providers[:imitators]
    return providers[0]


def _normalize_model_value(value: str | None) -> str | None:
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    parts = [part.strip() for part in re.split(r"[,\s]+", raw) if part.strip()]
    return parts[0] if parts else None


def resolve_config(
    *,
    api_key: str | None,
    base_url: str | None,
    model: str | None,
    temperature: float | None,
    mcp_config: str | None,
    workspace_dir: str | None = None,
    skills_dirs: Iterable[str] | None,
    skills_index: str | None,
    skills_priority: int | None,
    skills_groups: Iterable[str] | None = None,
    memory_dir: str | None,
    thread_id: str | None,
    stream: bool | None,
    imitator: str | None = None,
    system_prompt: str | None = None,
    context_max_tokens: int | None = None,
    summary_ratio: float | None = None,
    context_keep_last: int | None = None,
    debug: bool | None = None,
    use_skills: Iterable[str] | None = None,
    require_skills: Iterable[str] | None = None,
    fs_root: str | None = None,
    allow_write: bool | None = None,
    allow_scripts: bool | None = None,
    allow_shell: bool | None = None,
    shell_allowlist: Iterable[str] | None = None,
) -> AppConfig:
    _load_dotenv()

    cli_model = (model or "").strip() or None

    env_api_key = (os.getenv("VOIDCHAT_API_KEY") or "").strip()
    env_base_url = (os.getenv("VOIDCHAT_BASE_URL") or "").strip()
    env_model = (os.getenv("VOIDCHAT_MODEL") or "").strip()
    env_embedding = (os.getenv("VOIDCHAT_EMBEDDING_MODEL") or "").strip() or None
    env_system_prompt = (os.getenv("VOIDCHAT_SYSTEM_PROMPT") or "").strip()
    env_context_max_tokens = _parse_int(
        os.getenv("VOIDCHAT_CONTEXT_MAX_TOKENS"), DEFAULT_CONTEXT_MAX_TOKENS
    )
    env_summary_ratio = _parse_ratio(
        os.getenv("VOIDCHAT_SUMMARY_RATIO"), DEFAULT_SUMMARY_RATIO
    )
    env_context_keep_last = _parse_int(
        os.getenv("VOIDCHAT_CONTEXT_KEEP_LAST"), DEFAULT_CONTEXT_KEEP_LAST
    )
    env_debug = _parse_bool(os.getenv("VOIDCHAT_DEBUG"), DEFAULT_DEBUG)
    env_use_skills = _split_list(os.getenv("VOIDCHAT_USE_SKILLS"))
    env_require_skills = _split_list(os.getenv("VOIDCHAT_REQUIRE_SKILLS"))
    env_fs_root = (os.getenv("VOIDCHAT_FS_ROOT") or "").strip() or DEFAULT_FS_ROOT
    env_allow_write = _parse_bool(os.getenv("VOIDCHAT_ALLOW_WRITE"), DEFAULT_ALLOW_WRITE)
    env_allow_scripts = _parse_bool(os.getenv("VOIDCHAT_ALLOW_SCRIPTS"), DEFAULT_ALLOW_SCRIPTS)
    env_allow_shell = _parse_bool(os.getenv("VOIDCHAT_ALLOW_SHELL"), DEFAULT_ALLOW_SHELL)
    env_shell_allowlist = _split_list(os.getenv("VOIDCHAT_SHELL_ALLOWLIST"))
    env_mcp_config = os.getenv("VOIDCHAT_MCP_CONFIG") or default_mcp_config()
    env_workspace_dir = os.getenv("VOIDCHAT_WORKSPACE_DIR") or default_workspace_dir()
    env_skills = _split_paths(os.getenv("VOIDCHAT_SKILLS_DIR"))
    env_skills_index = (os.getenv("VOIDCHAT_SKILLS_INDEX") or "").strip()
    env_skills_groups = _split_paths(os.getenv("VOIDCHAT_SKILLS_GROUPS"))
    env_skills_priority = _parse_int(
        os.getenv("VOIDCHAT_SKILLS_PRIORITY"), DEFAULT_SKILLS_PRIORITY
    )
    env_memory_dir = os.getenv("VOIDCHAT_MEMORY_DIR") or default_memory_dir()

    resolved_api_key = api_key or env_api_key
    resolved_base_url = base_url or env_base_url
    resolved_model = model or env_model
    resolved_embedding = env_embedding
    resolved_system_prompt = system_prompt or env_system_prompt or DEFAULT_SYSTEM_PROMPT
    resolved_context_max_tokens = (
        context_max_tokens
        if context_max_tokens is not None
        else env_context_max_tokens
    )
    resolved_summary_ratio = (
        summary_ratio if summary_ratio is not None else env_summary_ratio
    )
    resolved_context_keep_last = (
        context_keep_last
        if context_keep_last is not None
        else env_context_keep_last
    )
    resolved_debug = env_debug if debug is None else debug
    resolved_fs_root = fs_root or env_fs_root or DEFAULT_FS_ROOT
    resolved_allow_write = env_allow_write if allow_write is None else bool(allow_write)
    resolved_allow_scripts = env_allow_scripts if allow_scripts is None else bool(allow_scripts)
    resolved_allow_shell = env_allow_shell if allow_shell is None else bool(allow_shell)
    if shell_allowlist is not None:
        resolved_shell_allowlist = _split_list(" ".join(list(shell_allowlist)))
    else:
        resolved_shell_allowlist = env_shell_allowlist or DEFAULT_SHELL_ALLOWLIST

    cli_use_skills = list(use_skills or [])
    cli_require_skills = list(require_skills or [])
    if cli_use_skills or cli_require_skills:
        resolved_use_skills = _split_list(" ".join(cli_use_skills))
        resolved_require_skills = _split_list(" ".join(cli_require_skills))
    else:
        resolved_use_skills = env_use_skills
        resolved_require_skills = env_require_skills
    resolved_skills_priority = (
        skills_priority if skills_priority is not None else env_skills_priority
    )

    provider = _resolve_provider_settings_override(imitator)
    if provider:
        if imitator:
            resolved_api_key = provider["api_key"]
            resolved_base_url = provider["base_url"]
            # --imitator sets provider defaults, but do NOT override an explicit model override
            if not cli_model and provider.get("completion_model"):
                resolved_model = provider["completion_model"]
            if provider.get("embedding_model"):
                resolved_embedding = provider["embedding_model"]
        else:
            if not resolved_api_key:
                resolved_api_key = provider["api_key"]
            if not resolved_base_url:
                resolved_base_url = provider["base_url"]
            if not resolved_model and provider.get("completion_model"):
                resolved_model = provider["completion_model"]
            if not resolved_embedding and provider.get("embedding_model"):
                resolved_embedding = provider["embedding_model"]

    if not resolved_api_key:
        resolved_api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not resolved_base_url:
        resolved_base_url = DEFAULT_BASE_URL
    if not resolved_model:
        resolved_model = DEFAULT_MODEL

    # skills_index template is optional; default to internal template (no AGENTS.md auto-discovery)
    resolved_skills_index = skills_index or env_skills_index or None

    cli_dirs = list(skills_dirs or [])
    cli_groups = list(skills_groups or [])
    if cli_dirs or cli_groups:
        resolved_skills = cli_dirs
        resolved_group_items = cli_groups
    else:
        resolved_skills = env_skills
        resolved_group_items = env_skills_groups

    resolved_groups = _parse_skills_groups(resolved_group_items, resolved_skills_priority)
    for path in resolved_skills:
        resolved_groups.append((resolved_skills_priority, path))

    if not resolved_groups and resolved_skills_index:
        index_root = os.path.dirname(resolved_skills_index)
        index_skills = os.path.join(index_root, DEFAULT_CLAUDE_SKILLS_DIR)
        if os.path.isdir(index_skills):
            resolved_groups.append((resolved_skills_priority, index_skills))

    if not resolved_groups:
        # Prefer `.voidchat/skills` if present (init-friendly), then `.claude/skills`.
        voidchat_skills = default_skills_dir()
        if os.path.isdir(voidchat_skills):
            resolved_groups.append((resolved_skills_priority, voidchat_skills))
        else:
            default_skills = _find_claude_skills_dir(os.getcwd())
            if default_skills:
                resolved_groups.append((resolved_skills_priority, default_skills))

    resolved_skills = [path for _, path in resolved_groups]

    return AppConfig(
        api_key=resolved_api_key,
        base_url=resolved_base_url,
        model=resolved_model,
        embedding_model=resolved_embedding,
        system_prompt=resolved_system_prompt,
        temperature=temperature if temperature is not None else 0.2,
        mcp_config=mcp_config or env_mcp_config,
        workspace_dir=workspace_dir or env_workspace_dir,
        skills_index=resolved_skills_index,
        skills_priority=resolved_skills_priority,
        skills_dirs=resolved_skills,
        skills_groups=resolved_groups,
        memory_dir=memory_dir or env_memory_dir,
        thread_id=thread_id or "default",
        stream=True if stream is None else stream,
        context_max_tokens=resolved_context_max_tokens,
        summary_ratio=resolved_summary_ratio,
        context_keep_last=resolved_context_keep_last,
        debug=resolved_debug,
        use_skills=resolved_use_skills,
        require_skills=resolved_require_skills,
        fs_root=resolved_fs_root,
        allow_write=resolved_allow_write,
        allow_scripts=resolved_allow_scripts,
        allow_shell=resolved_allow_shell,
        shell_allowlist=resolved_shell_allowlist,
    )


def _resolve_provider_settings_override(imitator: str | None) -> dict | None:
    """Resolve provider with optional CLI override.

    - If `imitator` provided, it is tried first (e.g. QWEN/ZHIPU).
    - Otherwise follow OPENAI_IMITATORS (list or numeric) or default prefixes.
    """
    forced = imitator.strip().upper() if imitator else None
    if forced:
        cfg = _provider_env(forced)
        if cfg:
            return cfg
    return _resolve_provider_settings()
