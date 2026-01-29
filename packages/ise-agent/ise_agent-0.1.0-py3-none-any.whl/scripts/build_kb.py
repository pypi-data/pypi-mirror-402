import os
import time
from collections import Counter
from config import DATA_SOURCE_DIR, CURATED_LINKS_FILE
from modules.document_loader import CourseDataLoader
from modules.noise import suppress_noisy_logs
from modules.vector_manager import VectorManager
from modules.pipeline import load_local_documents, load_curated_web_documents, build_vector_db


def main():
    start_time = time.time()
    suppress_noisy_logs()
    print("进入预处理阶段，开始扫描本地文档")
    loader = CourseDataLoader(quiet=True)
    v_manager = VectorManager()

    print(f"[-] 正在扫描本地目录: {DATA_SOURCE_DIR}")
    local_docs = load_local_documents(loader, DATA_SOURCE_DIR)
    local_count = Counter([d.metadata.get("course") or "Unknown" for d in local_docs])
    print("[-] 本地文档块（按课程统计）:")
    for k in sorted(local_count.keys()):
        print(f"    - {k}: {local_count[k]}")

    # 只加载手动筛选的链接（data/source/curated_links.txt）
    web_docs = load_curated_web_documents(loader, CURATED_LINKS_FILE, link_log_path=None)
    web_count = Counter([d.metadata.get("course") or "Unknown" for d in web_docs])
    print("[-] 网络文档块（按课程统计）:")
    for k in sorted(web_count.keys()):
        print(f"    - {k}: {web_count[k]}")

    all_docs = local_docs + web_docs
    total_count = Counter([d.metadata.get("course") or "Unknown" for d in all_docs])
    print("[-] 总文档块（按课程统计）:")
    for k in sorted(total_count.keys()):
        print(f"    - {k}: {total_count[k]}")

    if not all_docs:
        print("[!] 未找到任何文档，请检查网络或本地资料。")
        return

    build_vector_db(v_manager, all_docs)
    
    end_time = time.time()
    print(f"\n[+] 知识库构建完成！总耗时: {end_time - start_time:.2f} 秒")


if __name__ == "__main__":
    main()

