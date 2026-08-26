"""
career_memory.py - 职业军师长期档案存储脚本（占位）

功能规划：
1. 用户首次同意后创建职业档案（教育背景、工作经历、能力盘点、职业目标）
2. 跨任务压缩上下文召回
3. 关键事件自动更新（岗位变动、技能提升、薪酬变化）
4. 查看、暂停、撤销、删除

待实现：文件存储格式、字段定义、读写接口
"""

import json
import os
from datetime import datetime

MEMORY_DIR = os.path.join(os.path.dirname(__file__), "..", "memory")
PROFILE_FILE = os.path.join(MEMORY_DIR, "career_profile.json")


def init_profile():
    """初始化空档案"""
    return {
        "version": "1.0",
        "created_at": None,
        "updated_at": None,
        "consent": False,
        "education": {},
        "work_history": [],
        "skills": {"strengths": [], "gaps": []},
        "career_goal": None,
        "key_events": [],
        "mbti": None,
        "self_score": None,
    }


def load_profile():
    """加载档案"""
    if not os.path.exists(PROFILE_FILE):
        return None
    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_profile(profile):
    """保存档案"""
    os.makedirs(MEMORY_DIR, exist_ok=True)
    profile["updated_at"] = datetime.now().isoformat()
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)


def grant_consent(profile):
    """用户明确同意后启用"""
    profile["consent"] = True
    if not profile["created_at"]:
        profile["created_at"] = datetime.now().isoformat()
    save_profile(profile)


def revoke_consent(profile):
    """撤销同意，清除数据"""
    profile["consent"] = False
    profile["education"] = {}
    profile["work_history"] = []
    profile["skills"] = {"strengths": [], "gaps": []}
    profile["career_goal"] = None
    profile["key_events"] = []
    save_profile(profile)


def update_field(profile, field, value):
    """更新单个字段"""
    if not profile.get("consent"):
        return None
    profile[field] = value
    save_profile(profile)
    return profile


def add_key_event(profile, event):
    """添加关键事件"""
    if not profile.get("consent"):
        return None
    event["timestamp"] = datetime.now().isoformat()
    profile["key_events"].append(event)
    save_profile(profile)
    return profile


def get_compressed_context(profile):
    """获取压缩上下文用于召回"""
    if not profile or not profile.get("consent"):
        return None
    return {
        "education": profile.get("education"),
        "current_goal": profile.get("career_goal"),
        "mbti": profile.get("mbti"),
        "self_score": profile.get("self_score"),
        "recent_events": profile.get("key_events", [])[-5:],
    }


if __name__ == "__main__":
    print("career_memory.py - 职业军师档案存储脚本")
    print("此脚本需要通过 SKILL.md 流程调用，不建议单独运行。")
