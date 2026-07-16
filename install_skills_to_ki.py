import os
import shutil
import json
from datetime import datetime

# 配置路径
SOURCE_DIR = r"d:\Google(PH)\antigravity\6.8新手学习\superpowers-zh-main\skills"
KI_DIR = r"C:\Users\86134\.gemini\antigravity\knowledge"

# 指定需要安装的 9 个技能
TARGET_SKILLS = [
    "verification-before-completion",
    "systematic-debugging",
    "writing-plans",
    "executing-plans",
    "dispatching-parallel-agents",
    "writing-skills",
    "brainstorming",
    "test-driven-development",
    "chinese-documentation"
]

def install_skills():
    print("开始安装全局 AI 技能...")
    
    if not os.path.exists(KI_DIR):
        os.makedirs(KI_DIR)
        print(f"创建知识库目录: {KI_DIR}")

    success_count = 0

    for skill in TARGET_SKILLS:
        source_path = os.path.join(SOURCE_DIR, skill)
        target_path = os.path.join(KI_DIR, skill)
        artifacts_path = os.path.join(target_path, "artifacts")
        
        if not os.path.exists(source_path):
            print(f"警告: 找不到源技能文件夹 -> {skill}")
            continue
            
        # 创建目标 artifacts 目录
        if os.path.exists(target_path):
            shutil.rmtree(target_path)
        os.makedirs(artifacts_path)
        
        # 拷贝文件
        for item in os.listdir(source_path):
            s = os.path.join(source_path, item)
            d = os.path.join(artifacts_path, item)
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
                
        # 尝试从 SKILL.md 提取标题
        skill_md_path = os.path.join(artifacts_path, "SKILL.md")
        summary_text = f"Expert agentic skill: {skill}. Review artifacts/SKILL.md for execution details."
        if os.path.exists(skill_md_path):
            with open(skill_md_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if first_line.startswith("#"):
                    summary_text = f"Skill [{first_line.strip('# ')}]: Read artifacts/SKILL.md for instructions on how to use this skill."

        # 生成 metadata.json
        metadata = {
            "summary": summary_text,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "references": [f"Source: jnMetaCode/superpowers-zh/skills/{skill}"]
        }
        
        with open(os.path.join(target_path, "metadata.json"), 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
            
        print(f"✅ 成功安装技能: {skill}")
        success_count += 1
        
    print(f"\n安装完成！共成功写入 {success_count} 个全局技能至 KI 数据库。")

if __name__ == "__main__":
    install_skills()
