import os

# --- 基础配置 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_SOURCE_DIR = os.path.join(BASE_DIR, "data/source")
VECTOR_DB_DIR = os.path.join(BASE_DIR, "data/db")

# --- 本地大模型配置 ---
LOCAL_MODEL_NAME = os.getenv("LOCAL_MODEL_NAME", "Qwen/Qwen3-0.6B")
LOCAL_MODEL_REVISION = os.getenv("LOCAL_MODEL_REVISION", None)
DEVICE = os.getenv("LOCAL_DEVICE", "auto")

# --- API 模型配置 ---
# 可选: "local" (默认), "gemini", "qwen", "openai_compatible"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "qwen")

# 如果使用 qwen (通义千问 API)
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
QWEN_MODEL_NAME = "qwen-max"  # 可选: qwen-max, qwen-plus, qwen-turbo

# 如果使用 gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL_NAME = "gemini-1.5-flash"

# 如果使用 其他 OpenAI 兼容 API (如豆包、智谱等)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "qwen-max") 

# 生成参数
TEMPERATURE = 0.1
TOP_P = 0.9
TOP_K = 50
MAX_NEW_TOKENS = 800  # 调大，防止回答截断

# RAG 模式: strict (严谨但易答非所问), background (自然且允许补充)
RAG_MODE = os.getenv("RAG_MODE", "background").strip().lower()

# --- Embedding 配置 ---
EMBEDDING_PROVIDER = "huggingface" 
EMBEDDING_MODEL_NAME = "BAAI/bge-small-zh-v1.5"
HF_ENDPOINT = os.getenv("HF_ENDPOINT", "")  # 设置 https://hf-mirror.com

# --- RAG 配置 ---
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
RETRIEVAL_K = 6  # 增加检索数量，获取更全面的上下文

# --- 爬虫配置 ---
WEB_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
COURSE_URLS = {
    "CS231N": "https://cs231n.stanford.edu/schedule.html",
    "CS224N": "https://web.stanford.edu/class/archive/cs/cs224n/cs224n.1254/index.html#schedule",
    "CS336": "https://stanford-cs336.github.io/spring2025/index.html#schedule"
}

# 每门课最多抓取页面
CRAWL_MAX_PAGES = 30
CRAWL_LINKS_FILE = os.path.join(BASE_DIR, "data/logs/crawled_links.txt")

# 筛选后的链接清单
CURATED_LINKS_FILE = os.path.join(DATA_SOURCE_DIR, "curated_links.txt")

