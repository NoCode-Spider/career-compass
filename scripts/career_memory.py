"""
career_memory.py - 职业军师长期档案存储脚本

功能：
1. 用户首次同意后创建职业档案（教育背景、工作经历、能力盘点、职业目标等）
2. 跨任务压缩上下文召回
3. 关键事件自动记录（岗位变动、技能提升、薪酬变化、项目记录等）
4. 查看、暂停、撤销、删除档案
5. 项目记录、成果清单、技能清单、学习记录、反思总结

存储格式：本地 JSON 文件，纯本地，不上传任何数据。
隐私原则：默认不记录，用户明确同意后才启用，随时可以撤销和删除。
"""

import json
import os
from datetime import datetime

MEMORY_DIR = os.path.join(os.path.dirname(__file__), "..", "memory")
PROFILE_FILE = os.path.join(MEMORY_DIR, "career_profile.json")
BACKUP_DIR = os.path.join(MEMORY_DIR, "backups")

SCHEMA_VERSION = "2.0"


# ---------------------------------------------------------------------------
# 基础读写
# ---------------------------------------------------------------------------

def init_profile():
    """初始化一个空档案（用户同意后才创建）"""
    return {
        "version": SCHEMA_VERSION,
        "created_at": None,
        "updated_at": None,
        "consent": False,
        # 基本信息
        "basic_info": {
            "name": None,           # 昵称/代号（不强制用真名）
            "contact": None,        # 联系方式（可选）
            "current_status": None, # 在职/待业/读书/备考/自由职业
        },
        # 教育背景
        "education": [],           # [{school, major, degree, start_date, end_date, notes}]
        # 工作经历
        "work_history": [],        # [{company, position, department, start_date, end_date,
                                   #   report_to, reason_for_leaving, highlights}]
        # 当前工作（最近一份在职的）
        "current_job": None,       # 同上结构的当前版本
        # 技能清单
        "skills": {
            "strengths": [],       # [{skill, level, where_used, evidence}]
            "gaps": [],            # [{skill, importance, why, plan}]
            "certificates": [],    # [{name, issuer, date, expires}]
        },
        # 项目记录
        "projects": [],            # [{name, date_range, background, my_role,
                                   #   key_actions, results, challenges, learnings}]
        # 成果清单
        "achievements": [],        # [{date, achievement, data, project, category}]
        # 学习记录
        "learning_log": [],        # [{date, type, title, source, status, notes}]
        # 反馈记录
        "feedback_log": [],        # [{date, from, context, content, my_takeaway}]
        # 反思总结
        "reflections": [],         # [{date, period, highlights, lowlights,
                                   #   learnings, next_goals}]
        # 职业目标
        "career_goals": {
            "short_term": None,    # 1 年内
            "mid_term": None,      # 3 年
            "long_term": None,     # 5 年以上
            "progress_log": [],    # [{date, goal_type, update}]
        },
        # 测评记录
        "assessments": {
            "mbti": None,          # {type, date, source, notes}
            "holland": None,       # {result, date, source, notes}
            "big_five": None,      # {result, date, source, notes}
            "others": [],          # 其他测评
        },
        # 关键事件时间线
        "key_events": [],          # [{timestamp, type, description, impact}]
        # 自我评分（1-10）
        "self_score": None,
        # 人脉记录（可选，注意隐私）
        "network": [],             # [{name, role, company, how_we_met,
                                   #   area_of_expertise, last_contact}]
        # 杂项
        "notes": "",               # 自由文本备注
    }


def load_profile():
    """加载档案。如果不存在返回 None。"""
    if not os.path.exists(PROFILE_FILE):
        return None
    try:
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            profile = json.load(f)
        # 如果是旧版本，自动迁移
        if profile.get("version") != SCHEMA_VERSION:
            profile = _migrate_profile(profile)
        return profile
    except (json.JSONDecodeError, IOError):
        return None


def save_profile(profile):
    """保存档案，同时自动备份上一个版本。"""
    os.makedirs(MEMORY_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)

    profile["updated_at"] = datetime.now().isoformat()
    if not profile.get("created_at"):
        profile["created_at"] = profile["updated_at"]

    # 先备份当前文件（如果存在）
    if os.path.exists(PROFILE_FILE):
        backup_name = "career_profile_backup_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".json"
        backup_path = os.path.join(BACKUP_DIR, backup_name)
        try:
            with open(PROFILE_FILE, "r", encoding="utf-8") as src:
                with open(backup_path, "w", encoding="utf-8") as dst:
                    dst.write(src.read())
            # 只保留最近 10 个备份
            _cleanup_backups()
        except IOError:
            pass  # 备份失败不影响主流程

    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)


def _cleanup_backups():
    """清理备份文件，只保留最近 10 个"""
    if not os.path.exists(BACKUP_DIR):
        return
    backups = sorted(
        [f for f in os.listdir(BACKUP_DIR) if f.startswith("career_profile_backup_")],
        reverse=True,
    )
    for old in backups[10:]:
        try:
            os.remove(os.path.join(BACKUP_DIR, old))
        except OSError:
            pass


def _migrate_profile(old):
    """从旧版本档案迁移到新版本"""
    new = init_profile()
    # 复制所有存在的字段
    for key in old:
        if key in new and key != "version":
            new[key] = old[key]
    # v1 → v2 特殊迁移
    if old.get("version") == "1.0":
        # 旧版的 education 是 dict，新版是 list
        if isinstance(old.get("education"), dict) and old["education"]:
            new["education"] = [old["education"]]
        # 旧版的 career_goal 是字符串，新版是结构化的
        if old.get("career_goal") and isinstance(old["career_goal"], str):
            new["career_goals"]["short_term"] = old["career_goal"]
    new["version"] = SCHEMA_VERSION
    return new


# ---------------------------------------------------------------------------
# 同意管理（隐私第一）
# ---------------------------------------------------------------------------

def grant_consent(profile):
    """用户明确同意后启用档案记录"""
    profile["consent"] = True
    if not profile.get("created_at"):
        profile["created_at"] = datetime.now().isoformat()
    save_profile(profile)
    return profile


def revoke_consent(profile):
    """撤销同意 —— 清空所有数据，保留空壳（用户可以重新启用）"""
    empty = init_profile()
    empty["consent"] = False
    empty["created_at"] = profile.get("created_at")
    save_profile(empty)
    return empty


def delete_profile():
    """完全删除档案文件（不可恢复，除非有备份）"""
    if os.path.exists(PROFILE_FILE):
        # 删之前再备份一次到回收站目录
        trash_dir = os.path.join(BACKUP_DIR, "trash")
        os.makedirs(trash_dir, exist_ok=True)
        trash_name = "deleted_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".json"
        try:
            os.rename(PROFILE_FILE, os.path.join(trash_dir, trash_name))
        except OSError:
            os.remove(PROFILE_FILE)
        return True
    return False


def has_consent(profile):
    """检查是否已获得用户同意"""
    return bool(profile and profile.get("consent"))


# ---------------------------------------------------------------------------
# 字段更新辅助
# ---------------------------------------------------------------------------

def _safe_update(profile, section, key, value):
    """安全地更新嵌套字段，只有用户同意了才保存"""
    if not has_consent(profile):
        return None
    if section not in profile:
        profile[section] = {}
    profile[section][key] = value
    save_profile(profile)
    return profile


def _safe_append(profile, section, item):
    """安全地追加到列表，只有用户同意了才保存"""
    if not has_consent(profile):
        return None
    if section not in profile:
        profile[section] = []
    profile[section].append(item)
    save_profile(profile)
    return profile


# ---------------------------------------------------------------------------
# 基本信息
# ---------------------------------------------------------------------------

def set_basic_info(profile, field, value):
    """设置基本信息字段（name, contact, current_status 等）"""
    return _safe_update(profile, "basic_info", field, value)


# ---------------------------------------------------------------------------
# 教育背景
# ---------------------------------------------------------------------------

def add_education(profile, school, major, degree=None, start_date=None,
                  end_date=None, notes=None):
    """添加一条教育经历"""
    item = {
        "school": school,
        "major": major,
        "degree": degree,
        "start_date": start_date,
        "end_date": end_date,
        "notes": notes,
        "added_at": datetime.now().isoformat(),
    }
    return _safe_append(profile, "education", item)


# ---------------------------------------------------------------------------
# 工作经历
# ---------------------------------------------------------------------------

def add_work_history(profile, company, position, start_date, end_date=None,
                     department=None, report_to=None, reason_for_leaving=None,
                     highlights=None):
    """添加一条工作经历"""
    item = {
        "company": company,
        "position": position,
        "department": department,
        "start_date": start_date,
        "end_date": end_date,
        "report_to": report_to,
        "reason_for_leaving": reason_for_leaving,
        "highlights": highlights or [],
        "added_at": datetime.now().isoformat(),
    }
    return _safe_append(profile, "work_history", item)


def set_current_job(profile, company, position, start_date, department=None,
                    report_to=None):
    """设置当前工作"""
    if not has_consent(profile):
        return None
    profile["current_job"] = {
        "company": company,
        "position": position,
        "department": department,
        "start_date": start_date,
        "report_to": report_to,
        "updated_at": datetime.now().isoformat(),
    }
    save_profile(profile)
    return profile


# ---------------------------------------------------------------------------
# 技能
# ---------------------------------------------------------------------------

def add_strength(profile, skill, level=None, where_used=None, evidence=None):
    """添加一项优势技能"""
    item = {
        "skill": skill,
        "level": level,          # 入门/熟练/精通/专家
        "where_used": where_used,
        "evidence": evidence,
        "added_at": datetime.now().isoformat(),
    }
    if not has_consent(profile):
        return None
    profile["skills"]["strengths"].append(item)
    save_profile(profile)
    return profile


def add_skill_gap(profile, skill, importance=None, why=None, plan=None):
    """添加一项待提升技能"""
    item = {
        "skill": skill,
        "importance": importance,
        "why": why,
        "plan": plan,
        "added_at": datetime.now().isoformat(),
    }
    if not has_consent(profile):
        return None
    profile["skills"]["gaps"].append(item)
    save_profile(profile)
    return profile


def add_certificate(profile, name, issuer=None, date=None, expires=None):
    """添加一个证书"""
    item = {
        "name": name,
        "issuer": issuer,
        "date": date,
        "expires": expires,
        "added_at": datetime.now().isoformat(),
    }
    if not has_consent(profile):
        return None
    profile["skills"]["certificates"].append(item)
    save_profile(profile)
    return profile


# ---------------------------------------------------------------------------
# 项目记录
# ---------------------------------------------------------------------------

def add_project(profile, name, date_range=None, background=None, my_role=None,
                key_actions=None, results=None, challenges=None, learnings=None):
    """添加一个项目记录"""
    item = {
        "name": name,
        "date_range": date_range,
        "background": background,
        "my_role": my_role,
        "key_actions": key_actions or [],
        "results": results or [],
        "challenges": challenges,
        "learnings": learnings,
        "added_at": datetime.now().isoformat(),
    }
    return _safe_append(profile, "projects", item)


# ---------------------------------------------------------------------------
# 成果清单
# ---------------------------------------------------------------------------

def add_achievement(profile, achievement, date=None, data=None, project=None,
                    category=None):
    """添加一条量化成果"""
    item = {
        "date": date or datetime.now().strftime("%Y-%m-%d"),
        "achievement": achievement,
        "data": data,
        "project": project,
        "category": category,      # 业务/技术/管理/个人成长 等
        "added_at": datetime.now().isoformat(),
    }
    return _safe_append(profile, "achievements", item)


# ---------------------------------------------------------------------------
# 学习记录
# ---------------------------------------------------------------------------

def add_learning(profile, title, type_="book", source=None, status="completed",
                 notes=None, date=None):
    """添加一条学习记录"""
    item = {
        "date": date or datetime.now().strftime("%Y-%m-%d"),
        "type": type_,             # book/course/video/article/podcast
        "title": title,
        "source": source,
        "status": status,          # in_progress/completed/dropped
        "notes": notes,
        "added_at": datetime.now().isoformat(),
    }
    return _safe_append(profile, "learning_log", item)


# ---------------------------------------------------------------------------
# 反馈记录
# ---------------------------------------------------------------------------

def add_feedback(profile, content, from_whom=None, context=None,
                 my_takeaway=None, date=None):
    """添加一条反馈记录"""
    item = {
        "date": date or datetime.now().strftime("%Y-%m-%d"),
        "from": from_whom,
        "context": context,
        "content": content,
        "my_takeaway": my_takeaway,
        "added_at": datetime.now().isoformat(),
    }
    return _safe_append(profile, "feedback_log", item)


# ---------------------------------------------------------------------------
# 反思总结
# ---------------------------------------------------------------------------

def add_reflection(profile, period, highlights=None, lowlights=None,
                   learnings=None, next_goals=None, date=None):
    """添加一次反思总结（周/月/季度/年度）"""
    item = {
        "date": date or datetime.now().strftime("%Y-%m-%d"),
        "period": period,          # weekly/monthly/quarterly/yearly
        "highlights": highlights or [],
        "lowlights": lowlights or [],
        "learnings": learnings,
        "next_goals": next_goals or [],
        "added_at": datetime.now().isoformat(),
    }
    return _safe_append(profile, "reflections", item)


# ---------------------------------------------------------------------------
# 职业目标
# ---------------------------------------------------------------------------

def set_career_goal(profile, goal_type, goal_text):
    """设置职业目标（short_term/mid_term/long_term）"""
    if not has_consent(profile):
        return None
    if goal_type in ("short_term", "mid_term", "long_term"):
        profile["career_goals"][goal_type] = goal_text
        profile["career_goals"]["progress_log"].append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "goal_type": goal_type,
            "update": goal_text,
            "type": "set",
        })
        save_profile(profile)
    return profile


def update_goal_progress(profile, goal_type, progress_note):
    """记录目标进展"""
    if not has_consent(profile):
        return None
    profile["career_goals"]["progress_log"].append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "goal_type": goal_type,
        "update": progress_note,
        "type": "progress",
    })
    save_profile(profile)
    return profile


# ---------------------------------------------------------------------------
# 测评记录
# ---------------------------------------------------------------------------

def set_assessment(profile, assessment_type, result, date=None, source=None,
                   notes=None):
    """记录测评结果（mbti/holland/big_five/other）"""
    if not has_consent(profile):
        return None
    record = {
        "result": result,
        "date": date or datetime.now().strftime("%Y-%m-%d"),
        "source": source,
        "notes": notes,
    }
    if assessment_type in ("mbti", "holland", "big_five"):
        profile["assessments"][assessment_type] = record
    else:
        record["name"] = assessment_type
        profile["assessments"]["others"].append(record)
    save_profile(profile)
    return profile


# ---------------------------------------------------------------------------
# 关键事件
# ---------------------------------------------------------------------------

def add_key_event(profile, event_type, description, impact=None):
    """添加一个关键事件（升职/跳槽/降薪/重要项目/重大决策等）"""
    event = {
        "timestamp": datetime.now().isoformat(),
        "type": event_type,        # promotion/job_change/salary_change/
                                   # important_project/career_decision/other
        "description": description,
        "impact": impact,
    }
    return _safe_append(profile, "key_events", event)


# ---------------------------------------------------------------------------
# 人脉记录
# ---------------------------------------------------------------------------

def add_contact(profile, name, role=None, company=None, how_we_met=None,
                area_of_expertise=None, last_contact=None):
    """添加一条人脉记录（注意：不要记录隐私敏感信息）"""
    item = {
        "name": name,
        "role": role,
        "company": company,
        "how_we_met": how_we_met,
        "area_of_expertise": area_of_expertise,
        "last_contact": last_contact or datetime.now().strftime("%Y-%m-%d"),
        "added_at": datetime.now().isoformat(),
    }
    return _safe_append(profile, "network", item)


# ---------------------------------------------------------------------------
# 上下文召回（用于对话时快速获取关键信息）
# ---------------------------------------------------------------------------

def get_compressed_context(profile):
    """获取压缩版上下文，用于跨任务召回。
    只返回最关键的信息，不返回全量数据。"""
    if not has_consent(profile):
        return None

    ctx = {
        "basic_info": profile.get("basic_info", {}),
        "current_job": profile.get("current_job"),
        "work_history_count": len(profile.get("work_history", [])),
        "top_strengths": [s["skill"] for s in profile.get("skills", {}).get("strengths", [])[:5]],
        "top_gaps": [s["skill"] for s in profile.get("skills", {}).get("gaps", [])[:3]],
        "career_goals": {
            "short_term": profile.get("career_goals", {}).get("short_term"),
            "mid_term": profile.get("career_goals", {}).get("mid_term"),
        },
        "assessments": {
            "mbti": profile.get("assessments", {}).get("mbti", {}).get("result") if profile.get("assessments", {}).get("mbti") else None,
            "holland": profile.get("assessments", {}).get("holland", {}).get("result") if profile.get("assessments", {}).get("holland") else None,
        },
        "recent_events": [
            {"type": e.get("type"), "desc": e.get("description")}
            for e in profile.get("key_events", [])[-5:]
        ],
        "recent_projects": [
            p["name"] for p in profile.get("projects", [])[-3:]
        ],
        "achievements_count": len(profile.get("achievements", [])),
    }
    return ctx


def get_full_summary(profile):
    """获取完整档案的人类可读摘要（用于展示给用户确认）"""
    if not has_consent(profile):
        return "档案未启用或未获得用户同意。"

    lines = []
    lines.append("=== 职业档案概览 ===")
    lines.append(f"创建时间: {profile.get('created_at', '未知')}")
    lines.append(f"最近更新: {profile.get('updated_at', '未知')}")
    lines.append("")

    bi = profile.get("basic_info", {})
    lines.append(f"当前状态: {bi.get('current_status', '未设置')}")
    lines.append(f"教育经历: {len(profile.get('education', []))} 条")
    lines.append(f"工作经历: {len(profile.get('work_history', []))} 条")
    if profile.get("current_job"):
        cj = profile["current_job"]
        lines.append(f"当前工作: {cj.get('company', '')} - {cj.get('position', '')}")
    lines.append("")

    skills = profile.get("skills", {})
    lines.append(f"优势技能: {len(skills.get('strengths', []))} 项")
    lines.append(f"待提升技能: {len(skills.get('gaps', []))} 项")
    lines.append(f"证书: {len(skills.get('certificates', []))} 个")
    lines.append("")

    lines.append(f"项目记录: {len(profile.get('projects', []))} 个")
    lines.append(f"成果清单: {len(profile.get('achievements', []))} 条")
    lines.append(f"学习记录: {len(profile.get('learning_log', []))} 条")
    lines.append(f"反馈记录: {len(profile.get('feedback_log', []))} 条")
    lines.append(f"反思总结: {len(profile.get('reflections', []))} 次")
    lines.append(f"关键事件: {len(profile.get('key_events', []))} 条")
    lines.append(f"人脉记录: {len(profile.get('network', []))} 人")

    goals = profile.get("career_goals", {})
    if goals.get("short_term") or goals.get("mid_term") or goals.get("long_term"):
        lines.append("")
        lines.append("职业目标:")
        if goals.get("short_term"):
            lines.append(f"  短期: {goals['short_term']}")
        if goals.get("mid_term"):
            lines.append(f"  中期: {goals['mid_term']}")
        if goals.get("long_term"):
            lines.append(f"  长期: {goals['long_term']}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 导出
# ---------------------------------------------------------------------------

def export_profile(profile, format_type="json"):
    """导出档案（目前只支持 JSON，方便迁移）"""
    if format_type == "json":
        return json.dumps(profile, ensure_ascii=False, indent=2)
    return None


# ---------------------------------------------------------------------------
# 命令行入口（用于测试）
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("career_memory.py - 职业军师档案存储脚本")
    print("=" * 50)

    profile = load_profile()
    if profile is None:
        print("档案不存在。这是首次运行。")
        print("此脚本需要通过 SKILL.md 流程调用，不建议单独运行。")
    else:
        print(get_full_summary(profile))
        print()
        print("提示：档案存储位置:", PROFILE_FILE)
        print("如要查看压缩上下文，调用 get_compressed_context()")
