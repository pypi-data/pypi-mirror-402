"""
分支：数据预处理
功能：负责加载和解析各种来源的课程数据
"""

import os
import re
import json
import requests
import tempfile
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from config import WEB_USER_AGENT

class CourseDataLoader:
    def __init__(self, quiet: bool = True):
        self.quiet = quiet

    @staticmethod
    def _infer_course_and_chapter(file_path):
        """从路径/文件名推断课程名与章节号"""
        course = None
        chapter = None
        parts = file_path.replace("\\", "/").split("/")
        for p in parts:
            p2 = p.strip().lower()
            if p2 == "ise3309":
                course = "ISE3309"
                break
            if p2 == "cs336":
                course = "CS336"
                break
            if p2 == "cs224n":
                course = "CS224N"
                break
            if p2 == "cs231n":
                course = "CS231N"
                break

        filename = os.path.basename(file_path)
        m1 = re.search(r"Lecture\s*([0-9]+)", filename, re.IGNORECASE)
        if m1:
            chapter = f"Lecture{int(m1.group(1))}"
        else:
            m2 = re.match(r"^\s*([0-9]+)\s+", filename)
            if m2:
                chapter = f"Chapter{int(m2.group(1))}"
        return course, chapter

    @staticmethod
    def load_pdf(file_path, base_dir=None, chapter=None, course=None):
        """解析本地 PDF 课件"""
        try:
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            for doc in docs:
                rel_path = os.path.relpath(file_path, base_dir) if base_dir else os.path.basename(file_path)
                doc.metadata["source"] = f"Local_PDF: {rel_path}"
                if course:
                    doc.metadata["course"] = course
                if chapter:
                    doc.metadata["chapter"] = chapter
            return docs
        except Exception as e:
            print(f"Error loading PDF {file_path}: {e}")
            return []

    @staticmethod
    def load_notebook(file_path, base_dir=None, chapter=None, course=None):
        """解析本地 Jupyter Notebook (.ipynb)"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                raw = f.read()

            raw_stripped = raw.strip()

            # 兼容标准 ipynb：直接按 JSON 解析（避免依赖 nbformat 版本）
            if raw_stripped.startswith("{") and "\"cells\"" in raw:
                try:
                    data = json.loads(raw_stripped)
                    content = []
                    for cell in data.get("cells", []):
                        if cell.get("cell_type") not in ("markdown", "code"):
                            continue
                        src = cell.get("source", "")
                        if isinstance(src, list):
                            src = "".join(src)
                        if src:
                            content.append(src)
                    text = "\n\n".join(content) if content else raw
                except Exception:
                    # JSON 解析失败则回退为纯文本
                    text = raw
            else:
                # 非标准 ipynb 或导出文本：直接把文本当作笔记内容
                text = raw
            # 获取相对于 source 目录的路径，保留章节信息
            rel_path = os.path.relpath(file_path, base_dir) if base_dir else os.path.basename(file_path)
            return [Document(
                page_content=text,
                metadata={
                    "source": f"Local_Notebook: {rel_path}",
                    **({"course": course} if course else {}),
                    **({"chapter": chapter} if chapter else {}),
                }
            )]
        except Exception as e:
            print(f"Error loading Notebook {file_path}: {e}")
            return []

    @staticmethod
    def scrape_course_web(url, course_name):
        """爬取单个公开课程网页内容"""
        headers = {"User-Agent": WEB_USER_AGENT}
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            for tag in soup(['nav', 'footer', 'script', 'style', 'aside', 'header']):
                tag.decompose()
            main_content = soup.find('main') or soup.find('article') or soup.find('body')
            text = main_content.get_text(separator='\n', strip=True) if main_content else ""
            return [Document(
                page_content=text,
                metadata={"source": f"Web_Course: {course_name} ({url})"}
            )]
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return []

    @staticmethod
    def read_links_file(file_path: str) -> list[str]:
        # 读取手动筛选后的链接清单
        urls: list[str] = []
        if not file_path or not os.path.exists(file_path):
            return urls
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                urls.append(s)
        return urls

    @staticmethod
    def read_links_file_grouped(file_path: str) -> dict[str, list[str]]:
        # 读取分组链接文件（只接受合法课程名，避免把注释误判成分组）
        grouped: dict[str, list[str]] = {}
        if not file_path or not os.path.exists(file_path):
            return grouped

        current = None
        allowed = {"CS231N", "CS224N", "CS336", "ISE3309"}
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                s = line.strip()
                if not s:
                    continue
                if s.startswith("#"):
                    # 标题：# CS224N
                    title = s.lstrip("#").strip()
                    if title:
                        candidate = title.split()[0].upper()
                        if candidate in allowed:
                            current = candidate
                            grouped.setdefault(current, [])
                    continue
                if current:
                    grouped[current].append(s)
        return grouped

    @staticmethod
    def _write_crawled_links(link_log_path, course_name, links):
        if not link_log_path:
            return
        try:
            with open(link_log_path, "a", encoding="utf-8") as f:
                f.write(f"# {course_name}\n")
                for link in links:
                    f.write(f"{link}\n")
                f.write("\n")
        except Exception as e:
            print(f"Error writing crawled links for {course_name}: {e}")

    @staticmethod
    def _normalize_download_url(url: str) -> str:
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return url

            host = parsed.netloc.lower()
            if host in ("github.com", "www.github.com"):
                parts = parsed.path.strip("/").split("/")
                # /{owner}/{repo}/blob/{ref}/{path...}
                if len(parts) >= 5 and parts[2] == "blob":
                    owner, repo, ref = parts[0], parts[1], parts[3]
                    file_path = "/".join(parts[4:])
                    return f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{file_path}"
        except Exception:
            return url
        return url

    def _fetch_url_docs(self, url, course_name, headers):
        docs = []
        url = self._normalize_download_url(url)

        # 跳过明显的二进制资源（保留链接，但不尝试解析成文本）
        lower_url = url.lower()
        if lower_url.endswith((".zip", ".tar", ".tar.gz", ".tgz", ".gz", ".7z", ".rar")):
            return docs

        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "").lower()
        body = response.content
        text = response.text

        # JSON / trace：直接保存为文本
        if lower_url.endswith(".json") or "application/json" in content_type:
            txt = text if text is not None else body.decode("utf-8", errors="ignore")
            if txt:
                docs.append(Document(
                    page_content=txt,
                    metadata={"source": f"Web_JSON: {course_name} ({url})", "course": course_name}
                ))
            return docs

        if url.lower().endswith(".pdf") or "application/pdf" in content_type:
            # PDF：解析
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(body)
                tmp_path = tmp.name
            pdf_docs = self.load_pdf(tmp_path)
            for doc in pdf_docs:
                doc.metadata["source"] = f"Web_PDF: {course_name} ({url})"
                doc.metadata["course"] = course_name
            docs.extend(pdf_docs)
            os.unlink(tmp_path)
            return docs

        html = text if text is not None else body.decode("utf-8", errors="ignore")
        soup = BeautifulSoup(html, 'html.parser')
        for tag in soup(['nav', 'footer', 'script', 'style', 'aside', 'header']):
            tag.decompose()
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        text = main_content.get_text(separator='\n', strip=True) if main_content else ""
        if text:
            docs.append(Document(
                page_content=text,
                metadata={"source": f"Web_Course: {course_name} ({url})", "course": course_name}
            ))
        return docs

    def load_web_from_links(self, course_name: str, urls: list[str], link_log_path: str | None = None) -> list[Document]:
        """抓取给定的 URL 列表"""
        headers = {"User-Agent": WEB_USER_AGENT}
        docs: list[Document] = []
        crawled_links: list[str] = []
        for u in urls:
            if not u:
                continue
            try:
                u2 = self._normalize_download_url(u.strip())
                docs.extend(self._fetch_url_docs(u2, course_name, headers))
                crawled_links.append(u2)
            except Exception as e:
                print(f"Error scraping {u}: {e}")
                continue
        self._write_crawled_links(link_log_path, course_name, crawled_links)
        return docs

    @staticmethod
    def _cs336_should_keep_link(a_tag, next_url: str) -> bool:
        """
        CS336: 只保留 schedule 里的两类链接：
        - assignment 相关（code/preview/leaderboard 等通常都包含 assignment）
        - lecture_XX.py（实际点进去可能是 json/trace 等）
        其余全部舍弃。
        """
        href = (a_tag.get("href") or "").lower()
        text = (a_tag.get_text(" ", strip=True) or "").lower()
        url_l = (next_url or "").lower()

        # 丢弃 leaderboard / preview
        if "leaderboard" in href or "leaderboard" in text or "leaderboard" in url_l:
            return False
        if "preview" in href or "preview" in text or "preview" in url_l:
            return False

        # assignment
        if "assignment" in href or "assignment" in text or "assignment" in url_l:
            return True

        # lecture_01.py / lecture_02.py ...
        if re.search(r"lecture[_-]?\d+\.py\b", href) or re.search(r"lecture[_-]?\d+\.py\b", url_l):
            return True

        # 兼容 CS336 lectures trace json（有时会暴露在 schedule 链接里）
        if re.search(r"var/traces/lecture[_-]?\d+\.json\b", url_l) or re.search(r"lecture[_-]?\d+\.json\b", url_l):
            return True

        return False

    @staticmethod
    def _cs224n_should_keep_link(a_tag, next_url: str) -> bool:
        """
        CS224N: 只保留 schedule 里标注为 [slides] / [notes] / [code] 的外链接（大小写不敏感）。
        """
        text = (a_tag.get_text(" ", strip=True) or "").strip().lower()
        # 有些页面把方括号放在 <a> 标签外面，因此这里同时支持：
        # - "[slides]" / "[notes]" / "[code]"
        # - "slides" / "notes" / "code"
        return bool(re.match(r"^\[?\s*(slides|notes|code)\s*\]?$", text))

    def _scrape_schedule_links(
        self,
        schedule_url,
        course_name,
        max_pages=30,
        link_log_path=None,
        allow_external=False,
        link_filter=None,
    ):
        headers = {"User-Agent": WEB_USER_AGENT}
        schedule_url = schedule_url.strip()
        if not schedule_url.startswith("http"):
            schedule_url = "https://" + schedule_url.lstrip("/")

        docs = []
        crawled_links = []

        try:
            response = requests.get(schedule_url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            for tag in soup(['nav', 'footer', 'script', 'style', 'aside', 'header']):
                tag.decompose()
            main_content = soup.find('main') or soup.find('article') or soup.find('body')
            text = main_content.get_text(separator='\n', strip=True) if main_content else ""
            if text:
                docs.append(Document(
                    page_content=text,
                    metadata={"source": f"Web_Course: {course_name} ({schedule_url})"}
                ))
            crawled_links.append(schedule_url)

            schedule_container = soup.find(id=re.compile("schedule", re.IGNORECASE))
            if not schedule_container:
                schedule_container = soup.find(class_=re.compile("schedule", re.IGNORECASE))
            if not schedule_container:
                schedule_container = soup

            links = []
            seen = set()
            for a in schedule_container.find_all('a', href=True):
                href = a.get("href", "").strip()
                if not href:
                    continue
                if href.startswith(("mailto:", "javascript:")):
                    continue
                next_url = urljoin(schedule_url, href).split("#")[0]
                next_url = self._normalize_download_url(next_url)
                parsed = urlparse(next_url)
                if parsed.scheme not in ("http", "https"):
                    continue
                if not allow_external:
                    schedule_netloc = urlparse(schedule_url).netloc
                    if parsed.netloc != schedule_netloc:
                        continue
                if link_filter and not link_filter(a, next_url):
                    continue
                if next_url not in seen:
                    seen.add(next_url)
                    links.append(next_url)

            if max_pages:
                remaining = max_pages - len(crawled_links)
                if remaining < len(links):
                    links = links[:max(0, remaining)]

            for link in links:
                try:
                    docs.extend(self._fetch_url_docs(link, course_name, headers))
                    crawled_links.append(link)
                except Exception as e:
                    print(f"Error scraping {link}: {e}")
                    continue

        except Exception as e:
            print(f"Error scraping {schedule_url}: {e}")

        self._write_crawled_links(link_log_path, course_name, crawled_links)
        return docs

    def scrape_course_site(self, start_url, course_name, max_pages=30, link_log_path=None):
        """从课程主页出发，批量抓取讲义/页面内容"""
        course_upper = course_name.upper()
        if course_upper == "CS231N":
            return self._scrape_schedule_links(
                start_url,
                course_name,
                max_pages=max_pages,
                link_log_path=link_log_path,
            )
        if course_upper in ("CS224N", "CS336"):
            # CS336: 只保留 assignment + lecture_XX.py/trace json，其余外链舍弃
            if course_upper == "CS336":
                return self._scrape_schedule_links(
                    start_url,
                    course_name,
                    max_pages=max_pages,
                    link_log_path=link_log_path,
                    allow_external=True,
                    link_filter=self._cs336_should_keep_link,
                )
            # CS224N: 只保留 [slides]/[notes]/[code]
            return self._scrape_schedule_links(
                start_url,
                course_name,
                max_pages=max_pages,
                link_log_path=link_log_path,
                allow_external=True,
                link_filter=self._cs224n_should_keep_link,
            )
        headers = {"User-Agent": WEB_USER_AGENT}
        start_url = start_url.strip()
        if not start_url.startswith("http"):
            start_url = "https://" + start_url.lstrip("/")

        queue = [start_url]
        visited = set()
        docs = []
        page_count = 0
        pdf_count = 0
        crawled_links = []

        base = urlparse(start_url)
        base_netloc = base.netloc

        while queue and len(visited) < max_pages:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)

            try:
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                content_type = response.headers.get("Content-Type", "").lower()

                # 处理 PDF
                if url.lower().endswith(".pdf") or "application/pdf" in content_type:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(response.content)
                        tmp_path = tmp.name
                    pdf_docs = self.load_pdf(tmp_path)
                    for doc in pdf_docs:
                        doc.metadata["source"] = f"Web_PDF: {course_name} ({url})"
                    docs.extend(pdf_docs)
                    pdf_count += 1
                    os.unlink(tmp_path)
                    crawled_links.append(url)
                    continue

                soup = BeautifulSoup(response.text, 'html.parser')
                for tag in soup(['nav', 'footer', 'script', 'style', 'aside', 'header']):
                    tag.decompose()
                main_content = soup.find('main') or soup.find('article') or soup.find('body')
                text = main_content.get_text(separator='\n', strip=True) if main_content else ""

                if text:
                    docs.append(Document(
                        page_content=text,
                        metadata={"source": f"Web_Course: {course_name} ({url})"}
                    ))
                    page_count += 1
                crawled_links.append(url)

                # 解析并加入新链接
                for a in soup.find_all('a', href=True):
                    href = a.get("href")
                    if not href:
                        continue
                    next_url = urljoin(url, href)
                    next_url = next_url.split("#")[0]
                    parsed = urlparse(next_url)

                    if parsed.scheme not in ("http", "https"):
                        continue
                    if parsed.netloc != base_netloc:
                        continue

                    # 跳过常见非内容资源
                    if parsed.path.lower().endswith((
                        ".png", ".jpg", ".jpeg", ".gif", ".svg",
                        ".css", ".js", ".zip", ".ppt", ".pptx",
                        ".mp4", ".mp3"
                    )):
                        continue

                    if next_url not in visited and next_url not in queue:
                        queue.append(next_url)

            except Exception as e:
                print(f"Error scraping {url}: {e}")
                continue

        self._write_crawled_links(link_log_path, course_name, crawled_links)
        print(f"[抓取统计] {course_name}: 页面 {page_count}，PDF {pdf_count}，总文档块 {len(docs)}")
        return docs

    def load_all_local(self, directory):
        """扫描目录及其子目录下所有的 PDF 和 IPYNB 文件"""
        all_docs = []
        if not os.path.exists(directory):
            return all_docs

        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(":Zone.Identifier"):
                    continue
                path = os.path.join(root, file)
                if file.endswith('.pdf'):
                    course, chapter = self._infer_course_and_chapter(path)
                    all_docs.extend(self.load_pdf(path, base_dir=directory, chapter=chapter, course=course))
                elif file.endswith('.ipynb'):
                    course, chapter = self._infer_course_and_chapter(path)
                    parent = os.path.basename(os.path.dirname(path))
                    m = re.search(r"Lecture\s*([0-9]+)", parent, re.IGNORECASE)
                    if m:
                        chapter = f"Lecture{int(m.group(1))}"
                    all_docs.extend(self.load_notebook(path, base_dir=directory, chapter=chapter, course=course))

        return all_docs
