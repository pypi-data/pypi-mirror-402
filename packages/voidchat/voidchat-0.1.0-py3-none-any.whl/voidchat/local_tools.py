from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from glob import glob
from pathlib import Path


FENCE_RE = re.compile(r"```(?P<lang>[a-zA-Z0-9_-]+)?\n(?P<body>[\s\S]*?)\n```")


@dataclass(frozen=True)
class LocalToolConfig:
    fs_root: str
    repo_root: str
    allow_write: bool
    allow_scripts: bool
    allow_shell: bool
    shell_allowlist: list[str]


def _script_specs(config: LocalToolConfig) -> list[dict]:
    """Build an allowlisted script registry.

    This deliberately does NOT allow arbitrary commands; each entry is a fixed script runner.
    """
    repo = _abs_root(config.repo_root)

    def _p(rel: str) -> str:
        return str((repo / rel).resolve())

    py = sys.executable or "python3"
    node = shutil.which("node") or "node"
    pptx_toolkits = "projects/voidchat/pptx-toolkits"

    candidates = [
        {
            "name": "pptx.html2pptx",
            "description": "Render HTML slides to PPTX via html2pptx + pptxgenjs (node)",
            "argv": [node, _p(f"{pptx_toolkits}/scripts/html2pptx-run.js")],
            "cwd": "fs_root",
        },
        {
            "name": "pptx.inventory",
            "description": "Extract pptx text inventory (python)",
            "argv": [py, _p(f"{pptx_toolkits}/scripts/inventory.py")],
            "cwd": "fs_root",
        },
        {
            "name": "pptx.thumbnail",
            "description": "Create thumbnail grids from pptx (python)",
            "argv": [py, _p(f"{pptx_toolkits}/scripts/thumbnail.py")],
            "cwd": "fs_root",
        },
        {
            "name": "pptx.replace",
            "description": "Apply text replacements to pptx (python)",
            "argv": [py, _p(f"{pptx_toolkits}/scripts/replace.py")],
            "cwd": "fs_root",
        },
        {
            "name": "pptx.rearrange",
            "description": "Rearrange slides in pptx (python)",
            "argv": [py, _p(f"{pptx_toolkits}/scripts/rearrange.py")],
            "cwd": "fs_root",
        },
        {
            "name": "ooxml.unpack",
            "description": "Unpack Office file to directory (python)",
            "argv": [py, _p(f"{pptx_toolkits}/ooxml/scripts/unpack.py")],
            "cwd": "fs_root",
        },
        {
            "name": "ooxml.pack",
            "description": "Pack directory back to Office file (python)",
            "argv": [py, _p(f"{pptx_toolkits}/ooxml/scripts/pack.py")],
            "cwd": "fs_root",
        },
        {
            "name": "ooxml.validate",
            "description": "Validate OOXML directory against original file (python)",
            "argv": [py, _p(f"{pptx_toolkits}/ooxml/scripts/validate.py")],
            "cwd": "fs_root",
        },
    ]
    result = []
    for item in candidates:
        try:
            script_path = Path(item["argv"][1])
            if script_path.is_file():
                result.append(item)
        except Exception:
            continue
    return result


def script_list(config: LocalToolConfig, _args: dict) -> str:
    items = _script_specs(config)
    payload = [{"name": it["name"], "description": it["description"]} for it in items]
    return json.dumps({"scripts": payload}, ensure_ascii=False, indent=2)


def script_run(config: LocalToolConfig, args: dict) -> str:
    if not config.allow_scripts:
        return "脚本执行被禁止：请通过 --allow-scripts 或 VOIDCHAT_ALLOW_SCRIPTS=1 显式开启"
    name = str(args.get("name", "")).strip()
    extra = args.get("args", [])
    if not name:
        return "Missing required field: name"
    if extra is None:
        extra = []
    if not isinstance(extra, list) or not all(isinstance(x, str) for x in extra):
        return "Invalid field: args must be string[]"
    timeout_ms = int(args.get("timeout_ms", 30_000))
    max_chars = int(args.get("max_chars", 30_000))

    specs = {it["name"]: it for it in _script_specs(config)}
    spec = specs.get(name)
    if not spec:
        available = " ".join(sorted(specs.keys()))
        return f"Unknown script: {name}. Available: {available}"
    argv = list(spec["argv"]) + list(extra)

    cwd_root = _abs_root(config.fs_root if spec.get("cwd") == "fs_root" else config.repo_root)
    try:
        proc = subprocess.run(
            argv,
            cwd=str(cwd_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=max(1, timeout_ms) / 1000.0,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001
        msg = str(exc)
        if "No such file or directory" in msg and (" node" in msg or msg.endswith("'node'")):
            return (
                "script error: 未找到 node 可执行文件（请安装 Node.js，并确保 node 在 PATH 中可用）"
            )
        return f"script error: {exc}"

    payload = {"exit_code": proc.returncode, "stdout": proc.stdout or "", "stderr": proc.stderr or ""}
    if (
        "No module named 'PIL'" in payload["stderr"]
        or "No module named 'pptx'" in payload["stderr"]
        or "No module named 'lxml'" in payload["stderr"]
        or "No module named 'defusedxml'" in payload["stderr"]
    ):
        payload["hint"] = (
            "缺少依赖：建议安装 voidchat[pptx-tools]（或手动安装 python-pptx/pillow/six/lxml/defusedxml）后重试。"
        )
    if (
        "Cannot find module 'pptxgenjs'" in payload["stderr"]
        or "Cannot find module \"pptxgenjs\"" in payload["stderr"]
        or "Cannot find module 'playwright'" in payload["stderr"]
        or "Cannot find module \"playwright\"" in payload["stderr"]
        or "Cannot find module 'sharp'" in payload["stderr"]
        or "Cannot find module \"sharp\"" in payload["stderr"]
    ):
        payload["hint"] = (
            "缺少 Node 依赖：请在 "
            "projects/voidchat/pptx-toolkits/ "
            "目录安装依赖（npm/pnpm/yarn 均可）。"
            "Playwright 在某些环境还需要额外安装浏览器运行时；若报 chromium 相关错误，请按 Playwright 提示执行安装。"
        )
    if (
        "chromium.launch" in payload["stderr"]
        or "BrowserType.launch" in payload["stderr"]
        or "channel" in payload["stderr"] and "chrome" in payload["stderr"]
    ):
        payload.setdefault(
            "hint",
            "Playwright/Chromium 启动失败：macOS 默认会尝试使用本机 Chrome（channel=chrome）。"
            "请确认已安装 Google Chrome；或按 Playwright 提示安装浏览器运行时（例如安装 chromium）。",
        )
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    capped, _ = _cap(rendered, max_chars)
    return capped


def _abs_root(root: str) -> Path:
    # Do not require the path to exist; callers may point to workspace roots.
    return Path(root).expanduser().resolve()


def _resolve_in_root(root: Path, path: str) -> Path:
    raw = (path or "").strip()
    if not raw:
        raise ValueError("path 不能为空")
    p = Path(raw).expanduser()
    if p.is_absolute():
        resolved = p.resolve()
    else:
        resolved = (root / p).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("path 不允许越出 root") from exc
    return resolved


def _cap(text: str, max_chars: int) -> tuple[str, bool]:
    if max_chars <= 0:
        return text, False
    if len(text) <= max_chars:
        return text, False
    return text[:max_chars] + "\n...[truncated]...\n", True


def _load_text(path: Path, *, max_bytes: int = 2_000_000) -> str:
    if not path.is_file():
        raise ValueError("文件不存在")
    if path.stat().st_size > max_bytes:
        raise ValueError(f"文件过大（>{max_bytes} bytes），请用 offset/limit 分段读取")
    return path.read_text(encoding="utf-8", errors="replace")


def _slice_lines(text: str, offset: int | None, limit: int | None) -> str:
    if offset is None and limit is None:
        return text
    lines = text.splitlines()
    start = max(0, int(offset or 0))
    if limit is None:
        end = len(lines)
    else:
        end = max(start, start + max(0, int(limit)))
    sliced = lines[start:end]
    return "\n".join(sliced) + ("\n" if sliced else "")


def fs_read(config: LocalToolConfig, args: dict) -> str:
    root = _abs_root(config.fs_root)
    path = _resolve_in_root(root, str(args.get("path", "")))
    offset = args.get("offset", None)
    limit = args.get("limit", None)
    text = _load_text(path)
    return _slice_lines(text, offset, limit)


def repo_read(config: LocalToolConfig, args: dict) -> str:
    """Read a text file under repo_root (read-only)."""
    root = _abs_root(config.repo_root)
    path = _resolve_in_root(root, str(args.get("path", "")))
    offset = args.get("offset", None)
    limit = args.get("limit", None)
    text = _load_text(path)
    return _slice_lines(text, offset, limit)


def fs_list(config: LocalToolConfig, args: dict) -> str:
    root = _abs_root(config.fs_root)
    path = _resolve_in_root(root, str(args.get("path", ".")))
    if not path.is_dir():
        raise ValueError("目录不存在")
    limit = int(args.get("limit", 200))
    entries = []
    for name in sorted(os.listdir(path)):
        if name in {".", ".."}:
            continue
        entries.append(name)
        if len(entries) >= max(1, limit):
            entries.append("...[truncated]...")
            break
    return "\n".join(entries)


def fs_glob(config: LocalToolConfig, args: dict) -> str:
    root = _abs_root(config.fs_root)
    pattern = str(args.get("pattern", "")).strip()
    if not pattern:
        return "Missing required field: pattern"
    if os.path.isabs(pattern):
        return "pattern 不允许为绝对路径"
    if ".." in pattern:
        return "pattern 不允许包含 '..'"
    limit = int(args.get("limit", 200))
    base = str(root)
    matches = glob(os.path.join(base, pattern), recursive=True)
    # Return relative paths for readability
    rels: list[str] = []
    for m in sorted(set(matches)):
        p = Path(m).resolve()
        try:
            rels.append(str(p.relative_to(root)))
        except ValueError:
            continue
        if len(rels) >= max(1, limit):
            rels.append("...[truncated]...")
            break
    return "\n".join(rels)


def repo_glob(config: LocalToolConfig, args: dict) -> str:
    """Glob under repo_root (read-only)."""
    root = _abs_root(config.repo_root)
    pattern = str(args.get("pattern", "")).strip()
    if not pattern:
        return "Missing required field: pattern"
    if os.path.isabs(pattern):
        return "pattern 不允许为绝对路径"
    if ".." in pattern:
        return "pattern 不允许包含 '..'"
    limit = int(args.get("limit", 200))
    base = str(root)
    matches = glob(os.path.join(base, pattern), recursive=True)
    rels: list[str] = []
    for m in sorted(set(matches)):
        p = Path(m).resolve()
        try:
            rels.append(str(p.relative_to(root)))
        except ValueError:
            continue
        if len(rels) >= max(1, limit):
            rels.append("...[truncated]...")
            break
    return "\n".join(rels)


def fs_write(config: LocalToolConfig, args: dict) -> str:
    if not config.allow_write:
        return "写入被禁止：请通过 --allow-write 或 VOIDCHAT_ALLOW_WRITE=1 显式开启"
    root = _abs_root(config.fs_root)
    path = _resolve_in_root(root, str(args.get("path", "")))
    content = str(args.get("content", ""))
    overwrite = bool(args.get("overwrite", False))
    if path.exists() and not overwrite:
        return "文件已存在且 overwrite=false"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"ok: wrote {len(content)} chars to {path}"


def fs_replace_lines(config: LocalToolConfig, args: dict) -> str:
    if not config.allow_write:
        return "写入被禁止：请通过 --allow-write 或 VOIDCHAT_ALLOW_WRITE=1 显式开启"
    root = _abs_root(config.fs_root)
    path = _resolve_in_root(root, str(args.get("path", "")))
    start_line = int(args.get("start_line", 0))
    end_line = int(args.get("end_line", 0))
    new_text = str(args.get("new_text", ""))
    if start_line <= 0 or end_line <= 0 or end_line < start_line:
        return "行号非法：start_line/end_line 必须为正整数且 end_line>=start_line（1-based）"
    text = _load_text(path, max_bytes=10_000_000)
    lines = text.splitlines(keepends=True)
    if start_line > len(lines) + 1:
        return "start_line 超出文件范围"
    # Allow replacing past EOF by treating it as append.
    start_idx = max(0, start_line - 1)
    end_idx = min(len(lines), end_line)
    replacement = new_text.splitlines(keepends=True)
    if new_text and not replacement:
        replacement = [new_text]
    new_lines = lines[:start_idx] + replacement + lines[end_idx:]
    Path(path).write_text("".join(new_lines), encoding="utf-8")
    return f"ok: replaced lines {start_line}-{end_line} in {path}"


def text_extract_fence(_config: LocalToolConfig, args: dict) -> str:
    text = str(args.get("text", ""))
    lang = str(args.get("lang", "")).strip().lower()
    index = int(args.get("index", 0))
    matches = []
    for m in FENCE_RE.finditer(text):
        m_lang = (m.group("lang") or "").strip().lower()
        if lang and m_lang != lang:
            continue
        matches.append({"lang": m_lang, "content": m.group("body")})
    if not matches:
        return "no fenced code block found"
    index = max(0, min(index, len(matches) - 1))
    return matches[index]["content"]


def fs_search(config: LocalToolConfig, args: dict) -> str:
    root = _abs_root(config.fs_root)
    pattern = str(args.get("pattern", "")).strip()
    if not pattern:
        return "Missing required field: pattern"
    glob_pattern = str(args.get("glob", "")).strip() or None
    limit = int(args.get("limit", 50))
    max_chars = int(args.get("max_chars", 30_000))

    rg = shutil.which("rg")
    if rg:
        cmd = [rg, "-n", "--no-heading", "--color", "never", pattern, str(root)]
        if glob_pattern:
            cmd.extend(["--glob", glob_pattern])
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
                check=False,
            )
        except Exception as exc:  # noqa: BLE001
            return f"search error: {exc}"
        # rg returns 1 for no matches, 0 for matches
        out = (proc.stdout or "").strip()
        if not out:
            return "(no matches)"
        lines = out.splitlines()[: max(1, limit)]
        capped, _ = _cap("\n".join(lines), max_chars)
        return capped

    # Fallback: naive python scan (best-effort)
    hits: list[str] = []
    rx = re.compile(pattern)
    for p in root.rglob("*"):
        if p.is_dir():
            continue
        if glob_pattern and not p.match(glob_pattern):
            continue
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for i, line in enumerate(content.splitlines(), start=1):
            if rx.search(line):
                try:
                    rel = str(p.relative_to(root))
                except ValueError:
                    rel = str(p)
                hits.append(f"{rel}:{i}:{line}")
                if len(hits) >= max(1, limit):
                    capped, _ = _cap("\n".join(hits), max_chars)
                    return capped
                break
    return "(no matches)"


def shell_run(config: LocalToolConfig, args: dict) -> str:
    if not config.allow_shell:
        return "shell 被禁止：请通过 --allow-shell 或 VOIDCHAT_ALLOW_SHELL=1 显式开启"
    argv = args.get("argv")
    if not isinstance(argv, list) or not argv or not all(isinstance(x, str) for x in argv):
        return "Missing/invalid field: argv (string[])"
    cmd0 = argv[0].strip()
    allow = [c.strip() for c in (config.shell_allowlist or []) if c.strip()]
    if not allow:
        return "shell allowlist 为空：请设置 VOIDCHAT_SHELL_ALLOWLIST 或 --shell-allow"
    if cmd0 not in allow:
        return f"command not allowed: {cmd0}. allowed: {' '.join(allow)}"
    timeout_ms = int(args.get("timeout_ms", 10_000))
    max_chars = int(args.get("max_chars", 30_000))
    root = _abs_root(config.fs_root)
    try:
        proc = subprocess.run(
            argv,
            cwd=str(root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=max(1, timeout_ms) / 1000.0,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001
        return f"shell error: {exc}"
    payload = {
        "exit_code": proc.returncode,
        "stdout": proc.stdout or "",
        "stderr": proc.stderr or "",
    }
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    capped, _ = _cap(rendered, max_chars)
    return capped


def build_local_tools(config: LocalToolConfig) -> tuple[dict[str, object], list[dict]]:
    tools = {
        "voidchat_repo_read": lambda args: repo_read(config, args),
        "voidchat_repo_glob": lambda args: repo_glob(config, args),
        "voidchat_script_list": lambda args: script_list(config, args),
        "voidchat_script_run": lambda args: script_run(config, args),
        "voidchat_fs_read": lambda args: fs_read(config, args),
        "voidchat_fs_list": lambda args: fs_list(config, args),
        "voidchat_fs_glob": lambda args: fs_glob(config, args),
        "voidchat_fs_write": lambda args: fs_write(config, args),
        "voidchat_fs_replace_lines": lambda args: fs_replace_lines(config, args),
        "voidchat_fs_search": lambda args: fs_search(config, args),
        "voidchat_text_extract_fence": lambda args: text_extract_fence(config, args),
        "voidchat_shell": lambda args: shell_run(config, args),
    }

    schemas: list[dict] = [
        {
            "type": "function",
            "function": {
                "name": "voidchat_script_list",
                "description": "列出可用的脚本注册表（allowlisted runners）",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "voidchat_script_run",
                "description": "运行已注册脚本（非任意命令），用于调用准备好的 python/node/bash 脚本",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "脚本名，如 pptx.thumbnail"},
                        "args": {"type": "array", "items": {"type": "string"}, "description": "附加参数数组"},
                        "timeout_ms": {"type": "integer", "description": "超时毫秒（默认 30000）"},
                        "max_chars": {"type": "integer", "description": "最大返回字符数（默认 30000）"},
                    },
                    "required": ["name"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "voidchat_repo_read",
                "description": "读取仓库根目录(repo_root)下的文本文件（只读），可用 offset/limit 按行分段",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "相对 repo_root 的路径"},
                        "offset": {"type": "integer", "description": "从第几行开始（0-based）"},
                        "limit": {"type": "integer", "description": "读取多少行"},
                    },
                    "required": ["path"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "voidchat_repo_glob",
                "description": "按 glob 模式查找 repo_root 下的文件（只读；pattern 不允许绝对路径/..）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string", "description": "glob pattern，如 **/*.md"},
                        "limit": {"type": "integer", "description": "最多返回多少条（默认 200）"},
                    },
                    "required": ["pattern"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "voidchat_fs_read",
                "description": "读取 fs_root 下的文本文件（UTF-8），可用 offset/limit 按行分段",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "相对 fs_root 的路径"},
                        "offset": {"type": "integer", "description": "从第几行开始（0-based）"},
                        "limit": {"type": "integer", "description": "读取多少行"},
                    },
                    "required": ["path"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "voidchat_fs_list",
                "description": "列出 fs_root 下某个目录的子项（非递归）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "相对 fs_root 的目录路径"},
                        "limit": {"type": "integer", "description": "最多返回多少条（默认 200）"},
                    },
                    "required": ["path"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "voidchat_fs_glob",
                "description": "按 glob 模式查找 fs_root 下的文件（pattern 不允许绝对路径/..）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string", "description": "glob pattern，如 **/*.md"},
                        "limit": {"type": "integer", "description": "最多返回多少条（默认 200）"},
                    },
                    "required": ["pattern"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "voidchat_fs_write",
                "description": "写入文本文件（需要显式开启 allow_write），用于保存 md/svg 等",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "相对 fs_root 的路径"},
                        "content": {"type": "string", "description": "写入内容（UTF-8）"},
                        "overwrite": {"type": "boolean", "description": "是否覆盖已存在文件（默认 false）"},
                    },
                    "required": ["path", "content"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "voidchat_fs_replace_lines",
                "description": "按行号替换文件内容（1-based，含端点；需要 allow_write）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "相对 fs_root 的路径"},
                        "start_line": {"type": "integer", "description": "起始行号（1-based）"},
                        "end_line": {"type": "integer", "description": "结束行号（1-based）"},
                        "new_text": {"type": "string", "description": "替换文本"},
                    },
                    "required": ["path", "start_line", "end_line", "new_text"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "voidchat_fs_search",
                "description": "在 fs_root 下搜索文本（优先 rg；否则退化为 Python 扫描）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string", "description": "正则/字面模式（传给 rg 或 re）"},
                        "glob": {"type": "string", "description": "文件 glob 限制（可选），如 **/*.md"},
                        "limit": {"type": "integer", "description": "最多返回多少条（默认 50）"},
                        "max_chars": {"type": "integer", "description": "最大返回字符数（默认 30000）"},
                    },
                    "required": ["pattern"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "voidchat_text_extract_fence",
                "description": "从包含 ```lang``` ... ``` 的文本中提取 fenced code block（如 ```svg```），返回纯内容（注意：text 必须真的包含围栏）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "待解析文本"},
                        "lang": {"type": "string", "description": "语言过滤（可选），如 svg/md"},
                        "index": {"type": "integer", "description": "第几个匹配（默认 0）"},
                    },
                    "required": ["text"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "voidchat_shell",
                "description": "受控执行 allowlist 内的命令（不使用 shell；需要 allow_shell）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "argv": {"type": "array", "items": {"type": "string"}, "description": "命令参数数组，如 [\"rg\",\"foo\",\".\"]"},
                        "timeout_ms": {"type": "integer", "description": "超时毫秒（默认 10000）"},
                        "max_chars": {"type": "integer", "description": "最大返回字符数（默认 30000）"},
                    },
                    "required": ["argv"],
                    "additionalProperties": False,
                },
            },
        },
    ]
    return tools, schemas

