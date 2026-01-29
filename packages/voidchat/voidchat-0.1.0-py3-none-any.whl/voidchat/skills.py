from __future__ import annotations

from dataclasses import dataclass
import os
import re
import sys
from typing import Iterable

import yaml


SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SKILLS_TABLE_START = "<!-- SKILLS_TABLE_START -->"
SKILLS_TABLE_END = "<!-- SKILLS_TABLE_END -->"
USAGE_START = "<usage>"
USAGE_END = "</usage>"

DEFAULT_USAGE = """<usage>
Skills 是一组“可选的工作指令包”（每个 skill 对应一类任务的流程/约束）。
在当前对话中你会看到 skills 索引（<available_skills>）。

如何正确使用 skills：
- 先从索引里选择 **最相关的 1 个** skill（不要“遍历尝试”多个）
- 当你判断任务明显匹配某个 skill（例如：做 PPTX/处理 PDF/做前端设计/处理表格等）：先调用工具 `voidchat_skills_read` 读取该 skill 的完整正文指令，然后严格遵循执行
- 当用户明确要求使用某个 skill：同样先 `voidchat_skills_read` 再执行
- 若系统提示已包含该 skill 的完整正文（例如用户显式指定）：直接遵循执行，不要重复调用 `voidchat_skills_read`
- 若任务不需要任何 skill：不要强行套用

约束：
- 只能使用 <available_skills> 中列出的 skill 名称
- 不要假设存在 bash/openskills 之类的外部工具
</usage>"""


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    body: str
    source_path: str
    compatibility: str | None = None
    metadata: dict | None = None
    allowed_tools: list[str] | None = None


def _warn(message: str) -> None:
    print(f"[voidchat] skills: {message}", file=sys.stderr)


def _parse_frontmatter(raw: str) -> tuple[dict, str]:
    lines = raw.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, raw
    end_index = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_index = idx
            break
    if end_index is None:
        return {}, raw
    frontmatter = "\n".join(lines[1:end_index])
    body = "\n".join(lines[end_index + 1 :])
    try:
        meta = yaml.safe_load(frontmatter) or {}
    except yaml.YAMLError:
        return {}, body
    return meta, body


def _is_valid_name(name: str) -> bool:
    if not name or len(name) > 64:
        return False
    if name.startswith("-") or name.endswith("-") or "--" in name:
        return False
    return bool(SKILL_NAME_RE.fullmatch(name))


def _normalize_allowed_tools(value: object) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        return [item for item in value.split() if item]
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    return None


def _load_skill_file(path: str) -> Skill | None:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw = handle.read()
    except OSError:
        return None

    meta, body = _parse_frontmatter(raw)
    name = str(meta.get("name", "")).strip()
    description = str(meta.get("description", "")).strip()
    folder_name = os.path.basename(os.path.dirname(path))

    if not name or not description:
        _warn(f"SKILL.md 缺少必填 frontmatter: {path}")
        return None
    if not _is_valid_name(name):
        _warn(f"技能名称非法: {name} ({path})")
        return None
    if name != folder_name:
        _warn(f"技能名与目录不一致: {name} != {folder_name} ({path})")
        return None

    allowed_tools = _normalize_allowed_tools(meta.get("allowed-tools"))
    compatibility = str(meta.get("compatibility", "")).strip() or None
    metadata = meta.get("metadata")
    return Skill(
        name=name,
        description=description,
        body=body.strip(),
        source_path=path,
        compatibility=compatibility,
        metadata=metadata if isinstance(metadata, dict) else None,
        allowed_tools=allowed_tools,
    )


def _iter_skill_paths(root: str) -> list[str]:
    if os.path.isfile(root) and os.path.basename(root).lower() == "skill.md":
        return [root]
    if os.path.isdir(root):
        direct = os.path.join(root, "SKILL.md")
        if os.path.isfile(direct):
            return [direct]
        paths: list[str] = []
        for entry in os.listdir(root):
            # Skip template skeletons / hidden folders
            if entry.startswith(".") or entry in {"template"}:
                continue
            child = os.path.join(root, entry, "SKILL.md")
            if os.path.isfile(child):
                paths.append(child)
        return paths
    return []


def load_skills(skill_dirs: Iterable[str]) -> list[Skill]:
    skills: list[Skill] = []
    for root in skill_dirs:
        for path in _iter_skill_paths(root):
            skill = _load_skill_file(path)
            if skill:
                skills.append(skill)
    return skills


def render_skills_prompt(skills: Iterable[Skill]) -> str:
    blocks: list[str] = []
    for skill in skills:
        header = f"Skill: {skill.name}"
        desc = f"Description: {skill.description}"
        compatibility = f"Compatibility: {skill.compatibility}" if skill.compatibility else ""
        allowed = ""
        if skill.allowed_tools:
            allowed = f"Allowed tools: {' '.join(skill.allowed_tools)}"
        content = "\n".join(
            [line for line in [header, desc, compatibility, allowed, skill.body] if line]
        ).strip()
        if content:
            blocks.append(content)
    if not blocks:
        return ""
    return "\n\n---\n\n".join(blocks)


def render_skills_index(skills: Iterable[Skill]) -> str:
    lines = ["<available_skills>"]
    for skill in skills:
        lines.extend(
            [
                "<skill>",
                f"<name>{skill.name}</name>",
                f"<description>{skill.description}</description>",
                "<location>local</location>",
                "</skill>",
            ]
        )
    lines.append("</available_skills>")
    return "\n".join(lines)


def apply_skills_index_template(template_text: str, skills: Iterable[Skill]) -> str:
    if SKILLS_TABLE_START in template_text and SKILLS_TABLE_END in template_text:
        start = template_text.index(SKILLS_TABLE_START)
        end = template_text.index(SKILLS_TABLE_END) + len(SKILLS_TABLE_END)
        block = template_text[start:end]
        usage_block = _extract_usage_block(block) or DEFAULT_USAGE
        skills_block = render_skills_index(skills)
        merged = "\n".join([SKILLS_TABLE_START, usage_block, skills_block, SKILLS_TABLE_END])
        return template_text[:start] + merged + template_text[end:]
    return "\n\n".join([template_text.strip(), render_skills_index(skills)]).strip()


def _apply_skills_system_priority(template_text: str, priority: int) -> str:
    if "<skills_system" in template_text:
        return re.sub(
            r"<skills_system\\b[^>]*>",
            f'<skills_system priority="{priority}">',
            template_text,
            count=1,
        )
    return f'<skills_system priority="{priority}">\n{template_text}\n</skills_system>'


def _extract_usage_block(block: str) -> str | None:
    if USAGE_START in block and USAGE_END in block:
        start = block.index(USAGE_START)
        end = block.index(USAGE_END) + len(USAGE_END)
        return block[start:end]
    return None


def build_skills_prompt(
    skills_groups: Iterable[tuple[int, list[Skill]]],
    template_text: str | None,
    *,
    include_details: bool,
) -> str:
    groups = [(priority, skills) for priority, skills in skills_groups if skills]
    if not groups:
        return ""
    groups.sort(key=lambda item: item[0], reverse=True)

    blocks: list[str] = []
    for priority, skills in groups:
        if template_text:
            group_template = _apply_skills_system_priority(template_text, priority)
            index_prompt = apply_skills_index_template(group_template, skills)
            if include_details:
                details = render_skills_prompt(skills)
                if details:
                    blocks.append("\n\n".join([index_prompt, "Skill details:", details]).strip())
                else:
                    blocks.append(index_prompt.strip())
            else:
                blocks.append(index_prompt.strip())
        else:
            base = "\n".join([DEFAULT_USAGE, render_skills_index(skills)]).strip()
            base = _apply_skills_system_priority(base, priority)
            if include_details:
                details = render_skills_prompt(skills)
                if details:
                    blocks.append("\n\n".join([base, "Skill details:", details]).strip())
                else:
                    blocks.append(base)
            else:
                blocks.append(base)
    return "\n\n".join(blocks).strip()
