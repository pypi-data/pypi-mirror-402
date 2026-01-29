import os
from typing import Dict, List


def load_local_documents(loader, data_source_dir: str):
    # 加载本地文档
    return loader.load_all_local(data_source_dir)

def load_curated_web_documents(loader, curated_links_file: str, link_log_path: str | None = None):
    # 只抓取筛选后的链接（单文件分组）
    all_docs = []
    # 不写入链接日志（避免干扰 debug），除非显式指定
    if link_log_path:
        os.makedirs(os.path.dirname(link_log_path), exist_ok=True)
        with open(link_log_path, "w", encoding="utf-8") as f:
            f.write("")

    grouped = loader.read_links_file_grouped(curated_links_file)
    for course, urls in grouped.items():
        print(f"[-] 正在加载筛选后的链接: {course} ({len(urls)} 条)")
        all_docs.extend(loader.load_web_from_links(course, urls, link_log_path=link_log_path))
        print(f"    {course} 加载完成")

    return all_docs


def crawl_course_sites(loader, course_urls: Dict[str, str], max_pages: int, link_log_path: str | None = None):
    # 爬取课程讲义
    all_docs = []
    if link_log_path:
        os.makedirs(os.path.dirname(link_log_path), exist_ok=True)
        with open(link_log_path, "w", encoding="utf-8") as f:
            f.write("")
    for course, url in course_urls.items():
        print(f"[-] 正在爬取国外课程: {course}")
        web_docs = loader.scrape_course_site(url, course, max_pages=max_pages, link_log_path=link_log_path)
        all_docs.extend(web_docs)
        print(f"    {course} 爬取完成")
    return all_docs


def build_vector_db(vector_manager, documents):
    # 将文档写入向量库并持久化
    print("[-] 正在对文档进行分块并向量化存储...")
    vectordb = vector_manager.process_and_store(documents)
    print("[+] 知识库构建完成！")
    return vectordb

