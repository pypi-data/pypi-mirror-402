import os
import sys
from collections import Counter

# 允许导入项目模块
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from modules.vector_manager import VectorManager

def main():
    v_manager = VectorManager()
    vectordb = v_manager.load_vector_db()
    
    if not vectordb:
        print("[!] 向量数据库不存在，请先运行 scripts/build_kb.py")
        return

    # 获取所有文档的 metadata
    # 注意：Chroma 的 get() 方法如果不传 ids 会返回所有
    print("正在从数据库读取所有元数据...")
    data = vectordb.get(include=["metadatas"])
    metas = data.get("metadatas", [])
    
    if not metas:
        print("[!] 数据库是空的！")
        return

    print(f"\n[+] 数据库中共有 {len(metas)} 个文档块。")
    
    # 统计课程分布
    course_counts = Counter()
    source_types = Counter()
    
    for m in metas:
        # 优先使用 metadata 中的 course，如果没有则尝试从 source 推断
        course = m.get("course")
        if not course:
            src = m.get("source", "")
            if "ISE3309" in src: course = "ISE3309"
            elif "CS231N" in src: course = "CS231N"
            elif "CS224N" in src: course = "CS224N"
            elif "CS336" in src: course = "CS336"
            else: course = "Unknown"
        
        course_counts[course] += 1
        
        # 统计来源类型 (Web vs Local)
        src = m.get("source", "")
        if "Web_" in src:
            source_types["Web (网络爬取)"] += 1
        elif "Local_" in src:
            source_types["Local (本地文件)"] += 1
        else:
            source_types["Other"] += 1

    print("-" * 30)
    print("各课程块数量统计:")
    for course, count in course_counts.most_common():
        print(f"  - {course:10}: {count} 块")
    
    print("-" * 30)
    print("来源类型分布:")
    for stype, count in source_types.items():
        print(f"  - {stype:15}: {count} 块")

if __name__ == "__main__":
    main()

