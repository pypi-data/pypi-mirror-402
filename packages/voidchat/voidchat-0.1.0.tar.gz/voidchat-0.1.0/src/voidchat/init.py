from __future__ import annotations

from pathlib import Path
import shutil


def _find_voidchat_home_upwards(start: Path) -> Path | None:
    current = start.resolve()
    while True:
        candidate = current / ".voidchat"
        if candidate.is_dir():
            return candidate
        parent = current.parent
        if parent == current:
            return None
        current = parent


def _builtin_skills_dir() -> Path | None:
    """Best-effort locate bundled skills in repo checkout/editable install.

    In this monorepo, the authoritative bundled skills live under:
      projects/voidchat/.voidchat/skills (已归档；当前默认不再内置 skills)
    """
    project_root = Path(__file__).resolve().parents[2]
    candidate = project_root / ".voidchat" / "skills"
    return candidate if candidate.is_dir() else None


_MCP_TEMPLATE = """{
  "mcpServers": {}
}
"""

_ENV_EXAMPLE_TEMPLATE = """# OpenAI-compatible provider selection
OPENAI_IMITATORS=QWEN, OPENAI
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_API_KEY=YOUR_KEY
QWEN_COMPLETION_MODEL=qwen-plus
QWEN_EMBEDDING_MODEL=text-embedding-v3

# Optional overrides
VOIDCHAT_CONTEXT_MAX_TOKENS=8000
VOIDCHAT_SUMMARY_RATIO=0.5
VOIDCHAT_CONTEXT_KEEP_LAST=6
"""


def init_voidchat(
    *,
    local: bool,
    overwrite: bool,
    copy_skills: bool,
) -> None:
    """Initialize a `.voidchat/` directory for the current project."""
    cwd = Path.cwd()
    home = (cwd / ".voidchat").resolve() if local else (_find_voidchat_home_upwards(cwd) or (cwd / ".voidchat").resolve())

    home.mkdir(parents=True, exist_ok=True)
    (home / "memory").mkdir(parents=True, exist_ok=True)
    (home / "workspace").mkdir(parents=True, exist_ok=True)

    mcp_path = home / "mcp.json"
    if mcp_path.exists() and not overwrite:
        print(f"[voidchat] exists {mcp_path}")
    else:
        mcp_path.write_text(_MCP_TEMPLATE, encoding="utf-8")
        print(f"[voidchat] created {mcp_path}")

    env_example = cwd / ".env.example"
    if env_example.exists() and not overwrite:
        print(f"[voidchat] exists {env_example}")
    else:
        env_example.write_text(_ENV_EXAMPLE_TEMPLATE, encoding="utf-8")
        print(f"[voidchat] created {env_example}")

    if copy_skills:
        dst = home / "skills"
        src = _builtin_skills_dir()
        if not src:
            dst.mkdir(parents=True, exist_ok=True)
            print("[voidchat] skills: bundled source not found; created empty .voidchat/skills")
        else:
            if dst.exists() and not overwrite:
                print(f"[voidchat] exists {dst} (use --overwrite to refresh bundled skills)")
            else:
                if dst.exists() and overwrite:
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
                print(f"[voidchat] copied skills: {src} -> {dst}")

    print(f"[voidchat] init ok: {home}")

