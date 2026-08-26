#!/usr/bin/env python3
"""Validate the career-compass skill structure without third-party packages."""

from __future__ import annotations

import re
import sys
from math import ceil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ERRORS: list[str] = []
WARNINGS: list[str] = []
SKILL_MAX_LINES = 200
SKILL_MAX_CHARACTERS = 8_000
SKILL_MAX_APPROX_TOKENS = 6_000

# Knowledge base files (00-20)
REQUIRED_KNOWLEDGE = tuple(
    f"{i:02d}-{name}.md"
    for i, name in enumerate(
        [
            "知识库索引与撰写指南",
            "职业发展理论基础",
            "职业探索与决策模型",
            "工作满意度与投入理论",
            "频繁跳槽与心理契约",
            "职业倦怠与压力管理",
            "能力评估与技能迁移",
            "行业趋势与未来工作",
            "职业转换与过渡理论",
            "心理社会发展阶段",
            "自我效能与成长型思维",
            "学习科学与方法论",
            "中国就业市场与劳动法",
            "薪酬结构与市场定价",
            "职场人际与向上管理",
            "远程工作与数字游民",
            "创业与自由职业可行性",
            "职场多样性与公平",
            "心理健康与职场适应",
            "职业测评工具解析",
            "核心书单与论文索引",
        ]
    )
)

# Practical guides (00-23)
REQUIRED_PRACTICAL = tuple(
    f"{i:02d}-{name}.md"
    for i, name in enumerate(
        [
            "导读与使用分级",
            "简历优化与投递策略",
            "面试技巧与模拟演练",
            "薪酬谈判实战指南",
            "离职决策与流程",
            "跳槽时机与策略",
            "职业转型路径设计",
            "技能盘点与差距分析",
            "行业调研方法",
            "职场新人90天生存指南",
            "向上管理与职场沟通",
            "职业倦怠自救指南",
            "工作生活平衡实践",
            "副业与自由职业起步",
            "创业可行性评估",
            "个人品牌建设",
            "升职加薪策略",
            "转行完全指南",
            "应届生求职特殊指南",
            "职场冲突处理指南",
            "远程工作效率指南",
            "求职心态管理指南",
            "长期记忆与职业档案",
            "职业测评解读指南",
        ]
    )
)


def require(path: str) -> Path:
    target = ROOT / path
    if not target.exists():
        ERRORS.append(f"missing required path: {path}")
    return target


def validate_frontmatter() -> None:
    skill = require("SKILL.md")
    if not skill.is_file():
        return

    content = skill.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not match:
        ERRORS.append("SKILL.md has invalid YAML frontmatter boundaries")
        return

    frontmatter = match.group(1)
    keys = re.findall(r"^([A-Za-z0-9_-]+):", frontmatter, re.MULTILINE)
    if keys != ["name", "description"]:
        ERRORS.append(f"SKILL.md frontmatter keys must be name, description; got {keys}")

    name_match = re.search(r"^name:\s*([^\n]+)$", frontmatter, re.MULTILINE)
    description_match = re.search(r"^description:\s*(.+)$", frontmatter, re.MULTILINE)
    name = name_match.group(1).strip() if name_match else ""
    description = description_match.group(1).strip() if description_match else ""
    if name != "career-compass" or not re.fullmatch(r"[a-z0-9-]{1,64}", name):
        ERRORS.append(f"invalid skill name: {name!r}")
    if not description or len(description) > 1024 or "<" in description or ">" in description:
        ERRORS.append("description is empty, too long, or contains angle brackets")


def approximate_token_count(content: str) -> int:
    """Return a conservative, dependency-free budget estimate for mixed Chinese text."""
    cjk = len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]", content))
    latin_words = len(re.findall(r"[A-Za-z0-9_]+", content))
    other = len(re.findall(r"[^\sA-Za-z0-9_\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]", content))
    return cjk + ceil(latin_words * 1.3) + ceil(other / 4)


def validate_skill_budget() -> None:
    skill = ROOT / "SKILL.md"
    if not skill.is_file():
        return

    content = skill.read_text(encoding="utf-8")
    lines = len(content.splitlines())
    characters = len(content)
    approx_tokens = approximate_token_count(content)
    print(f"  SKILL.md: {lines} lines, {characters} chars, ~{approx_tokens} tokens")
    if lines > SKILL_MAX_LINES:
        WARNINGS.append(f"SKILL.md exceeds {SKILL_MAX_LINES} lines: {lines}")
    if characters > SKILL_MAX_CHARACTERS:
        WARNINGS.append(
            f"SKILL.md exceeds {SKILL_MAX_CHARACTERS} characters: {characters}"
        )
    if approx_tokens > SKILL_MAX_APPROX_TOKENS:
        WARNINGS.append(
            "SKILL.md exceeds approximate token budget "
            f"{SKILL_MAX_APPROX_TOKENS}: {approx_tokens}"
        )


def validate_inventory() -> None:
    require("agents/openai.yaml")
    require("scripts/career_memory.py")
    require("README.md")

    for filename in REQUIRED_KNOWLEDGE:
        require(f"references/knowledge/{filename}")
    for filename in REQUIRED_PRACTICAL:
        require(f"references/practical/{filename}")

    agent = ROOT / "agents/openai.yaml"
    if agent.is_file():
        agent_text = agent.read_text(encoding="utf-8")
        if "$career-compass" not in agent_text and "career-compass" not in agent_text:
            WARNINGS.append("agents/openai.yaml may not reference career-compass")


def validate_routes() -> None:
    skill = ROOT / "SKILL.md"
    if not skill.is_file():
        return

    content = skill.read_text(encoding="utf-8")

    # Core framework markers
    framework_markers = [
        "情绪落地",
        "现状拆分",
        "利益判断",
        "明确建议",
        "行动收束",
        "停止条件",
    ]
    for marker in framework_markers:
        if marker not in content:
            ERRORS.append(f"SKILL.md missing core framework section: {marker}")

    # Safety boundaries
    safety_markers = [
        "不诊断心理疾病",
        "不鼓励无计划的裸辞",
        "不协助简历造假",
        "职场霸凌",
    ]
    for marker in safety_markers:
        if marker not in content:
            WARNINGS.append(f"SKILL.md missing safety boundary mention: {marker}")

    # First-use questionnaire
    if "先让我认识你和你的职业现状" not in content:
        WARNINGS.append("SKILL.md may be missing first-use questionnaire")


def validate_markdown_links() -> None:
    link_pattern = re.compile(r"\]\(([^)]+)\)")
    broken_count = 0
    for markdown in ROOT.rglob("*.md"):
        text = markdown.read_text(encoding="utf-8")
        for raw_target in link_pattern.findall(text):
            target = raw_target.strip().split("#", 1)[0]
            if not target or re.match(r"^(?:https?://|mailto:)", target):
                continue
            resolved = (markdown.parent / target).resolve()
            if not resolved.exists():
                broken_count += 1
                WARNINGS.append(
                    f"broken local link in {markdown.relative_to(ROOT)}: {raw_target}"
                )
    if broken_count:
        WARNINGS.append(f"Total broken links: {broken_count}")


def validate_placeholders() -> None:
    todo_count = 0
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix.lower() not in {".md", ".yaml", ".yml", ".py"}:
            continue
        text = path.read_text(encoding="utf-8")
        if "TODO" in text or "todo" in text.lower() and "待" in text:
            todo_count += 1
            WARNINGS.append(f"potential TODO placeholder in {path.relative_to(ROOT)}")


def validate_content_quality() -> None:
    """Basic content quality checks."""
    knowledge_dir = ROOT / "references" / "knowledge"
    practical_dir = ROOT / "references" / "practical"

    short_files = []
    for md_file in list(knowledge_dir.glob("*.md")) + list(practical_dir.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        if len(content.strip()) < 500:
            short_files.append(md_file.relative_to(ROOT))

    if short_files:
        WARNINGS.append(
            f"Files with very short content (<500 chars): {len(short_files)}"
        )
        for f in short_files[:5]:
            WARNINGS.append(f"  - {f}")


def main() -> int:
    print("=" * 50)
    print("career-compass Skill Validation")
    print("=" * 50)

    print("\n[1/7] Validating frontmatter...")
    validate_frontmatter()

    print("[2/7] Validating SKILL.md budget...")
    validate_skill_budget()

    print("[3/7] Validating file inventory...")
    validate_inventory()
    knowledge_count = len(list((ROOT / "references" / "knowledge").glob("*.md")))
    practical_count = len(list((ROOT / "references" / "practical").glob("*.md")))
    print(f"  Knowledge files: {knowledge_count}")
    print(f"  Practical files: {practical_count}")

    print("[4/7] Validating routes and framework...")
    validate_routes()

    print("[5/7] Validating markdown links...")
    validate_markdown_links()

    print("[6/7] Checking for placeholders...")
    validate_placeholders()

    print("[7/7] Checking content quality...")
    validate_content_quality()

    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)

    if ERRORS:
        print(f"\n❌ ERRORS ({len(ERRORS)}):")
        for error in ERRORS:
            print(f"   - {error}")

    if WARNINGS:
        print(f"\n⚠️  WARNINGS ({len(WARNINGS)}):")
        for warning in WARNINGS:
            print(f"   - {warning}")

    if not ERRORS and not WARNINGS:
        print("\n✅ All checks passed!")
    elif not ERRORS:
        print(f"\n✅ Validation passed with {len(WARNINGS)} warnings.")
    else:
        print(f"\n❌ Validation failed with {len(ERRORS)} errors and {len(WARNINGS)} warnings.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
