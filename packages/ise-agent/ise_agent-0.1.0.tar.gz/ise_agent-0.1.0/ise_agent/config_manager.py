"""配置管理模块 - 处理用户配置的读写"""
import os
import json
from pathlib import Path
from typing import Dict, Optional

# 配置文件的默认位置（用户主目录下的 .ise_agent_config.json）
CONFIG_FILE = Path.home() / ".ise_agent_config.json"

# 默认配置
DEFAULT_CONFIG = {
    "llm_provider": "qwen",  # local, gemini, qwen, openai_compatible
    "qwen_api_key": "",
    "qwen_model_name": "qwen-max",
    "gemini_api_key": "",
    "gemini_model_name": "gemini-1.5-flash",
    "openai_api_key": "",
    "openai_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "openai_model_name": "qwen-max",
    "local_model_name": "Qwen/Qwen3-0.6B",
    "device": "auto",
    "hf_endpoint": "",  # HuggingFace 镜像站
}

def load_config() -> Dict:
    """加载配置文件"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 合并默认配置，确保所有字段都存在
                merged = DEFAULT_CONFIG.copy()
                merged.update(config)
                return merged
        except Exception as e:
            print(f"⚠️  读取配置文件失败: {e}，使用默认配置")
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()

def save_config(config: Dict) -> bool:
    """保存配置到文件"""
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ 保存配置文件失败: {e}")
        return False

def apply_config_to_env(config: Dict):
    """将配置应用到环境变量（供 config.py 读取）"""
    os.environ["LLM_PROVIDER"] = config.get("llm_provider", "qwen")
    os.environ["QWEN_API_KEY"] = config.get("qwen_api_key", "")
    os.environ["QWEN_MODEL_NAME"] = config.get("qwen_model_name", "qwen-max")
    os.environ["GEMINI_API_KEY"] = config.get("gemini_api_key", "")
    os.environ["GEMINI_MODEL_NAME"] = config.get("gemini_model_name", "gemini-1.5-flash")
    os.environ["OPENAI_API_KEY"] = config.get("openai_api_key", "")
    os.environ["OPENAI_BASE_URL"] = config.get("openai_base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    os.environ["OPENAI_MODEL_NAME"] = config.get("openai_model_name", "qwen-max")
    os.environ["LOCAL_MODEL_NAME"] = config.get("local_model_name", "Qwen/Qwen3-0.6B")
    os.environ["LOCAL_DEVICE"] = config.get("device", "auto")
    if config.get("hf_endpoint"):
        os.environ["HF_ENDPOINT"] = config["hf_endpoint"]

