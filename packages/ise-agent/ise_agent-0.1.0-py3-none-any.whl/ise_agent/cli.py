"""命令行入口 - 支持交互式配置和启动对话"""
import os
import sys
import re
import time
from pathlib import Path

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ise_agent.config_manager import load_config, save_config, apply_config_to_env, CONFIG_FILE
from modules.vector_manager import VectorManager
from modules.noise import suppress_noisy_logs
from modules.rag_engine import CourseAssistantAgent

# 颜色配置
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
GREY = "\033[90m"
BOLD = "\033[1m"
UNDERLINE = "\033[4m"
END = "\033[0m"

def render_styled_text(text):
    """终端美化渲染"""
    text = re.sub(r"# (.*)", f"{BOLD}{CYAN}# \\1{END}", text)
    text = re.sub(r"\*\*(.*?)\*\*", f"{BOLD}{GREEN}\\1{END}", text)
    text = re.sub(r"^> (.*)", f"{GREY}▎ \\1{END}", text, flags=re.MULTILINE)
    text = re.sub(r"(https?://[^\s\)]+)", f"{UNDERLINE}{BLUE}\\1{END}", text)
    return text

def interactive_config():
    """交互式配置向导"""
    print(f"\n{BOLD}{CYAN}=== ISE3309 智能助教配置向导 ==={END}\n")
    
    config = load_config()
    
    # 1. 选择 LLM Provider
    print(f"{BOLD}1. 选择大语言模型提供商：{END}")
    print(f"   {GREY}[1] 通义千问 (Qwen) - 推荐{END}")
    print(f"   {GREY}[2] Google Gemini{END}")
    print(f"   {GREY}[3] OpenAI 兼容 API (如豆包、智谱等){END}")
    print(f"   {GREY}[4] 本地模型 (需要下载模型，较慢){END}")
    
    choice = input(f"\n请选择 [1-4] (当前: {config.get('llm_provider')}): ").strip()
    
    if choice == "1" or (not choice and config.get('llm_provider') == 'qwen'):
        config["llm_provider"] = "qwen"
        api_key = input(f"请输入 Qwen API Key (当前: {'已设置' if config.get('qwen_api_key') else '未设置'}): ").strip()
        if api_key:
            config["qwen_api_key"] = api_key
        
        model_choice = input(f"选择模型 [1] qwen-max [2] qwen-plus [3] qwen-turbo (当前: {config.get('qwen_model_name')}): ").strip()
        if model_choice == "2":
            config["qwen_model_name"] = "qwen-plus"
        elif model_choice == "3":
            config["qwen_model_name"] = "qwen-turbo"
        else:
            config["qwen_model_name"] = "qwen-max"
            
    elif choice == "2":
        config["llm_provider"] = "gemini"
        api_key = input(f"请输入 Gemini API Key (当前: {'已设置' if config.get('gemini_api_key') else '未设置'}): ").strip()
        if api_key:
            config["gemini_api_key"] = api_key
            
    elif choice == "3":
        config["llm_provider"] = "openai_compatible"
        api_key = input(f"请输入 API Key (当前: {'已设置' if config.get('openai_api_key') else '未设置'}): ").strip()
        if api_key:
            config["openai_api_key"] = api_key
        
        base_url = input(f"请输入 Base URL (当前: {config.get('openai_base_url')}): ").strip()
        if base_url:
            config["openai_base_url"] = base_url
            
        model_name = input(f"请输入模型名称 (当前: {config.get('openai_model_name')}): ").strip()
        if model_name:
            config["openai_model_name"] = model_name
            
    elif choice == "4":
        config["llm_provider"] = "local"
        model_name = input(f"请输入本地模型名称 (当前: {config.get('local_model_name')}): ").strip()
        if model_name:
            config["local_model_name"] = model_name
            
    # 2. HuggingFace 镜像（可选）
    print(f"\n{BOLD}2. HuggingFace 镜像站（可选，用于加速下载）：{END}")
    print(f"   {GREY}留空跳过，或输入镜像站地址，例如: https://hf-mirror.com{END}")
    hf_endpoint = input(f"镜像站地址 (当前: {config.get('hf_endpoint') or '未设置'}): ").strip()
    if hf_endpoint:
        config["hf_endpoint"] = hf_endpoint
    elif not config.get("hf_endpoint"):
        config["hf_endpoint"] = ""
    
    # 保存配置
    if save_config(config):
        print(f"\n{GREEN}✓ 配置已保存到: {CONFIG_FILE}{END}")
        print(f"{GREY}下次运行时会自动加载此配置。如需修改，请删除配置文件重新配置。{END}")
    else:
        print(f"\n{YELLOW}⚠️  配置保存失败，但可以继续使用（本次会话有效）{END}")
    
    return config

def check_and_setup_config():
    """检查配置，如果不存在或需要更新则启动向导"""
    config = load_config()
    
    # 检查必需的配置
    provider = config.get("llm_provider", "qwen")
    needs_config = False
    
    if provider == "qwen" and not config.get("qwen_api_key"):
        needs_config = True
    elif provider == "gemini" and not config.get("gemini_api_key"):
        needs_config = True
    elif provider == "openai_compatible" and not config.get("openai_api_key"):
        needs_config = True
    
    if needs_config or not CONFIG_FILE.exists():
        print(f"\n{YELLOW}[!] 检测到未配置或配置不完整，启动配置向导...{END}")
        config = interactive_config()
    
    # 应用配置到环境变量
    apply_config_to_env(config)
    return config

def main():
    """主函数"""
    suppress_noisy_logs()
    
    # 检查并设置配置
    config = check_and_setup_config()
    
    # 统计初始化时间
    init_start = time.time()
    print(f"\n{BOLD}{CYAN}=== 正在初始化 ISE3309 智能助教系统... ==={END}")
    
    # 检查向量数据库位置
    # 在安装模式下，数据库应该在用户目录或包目录下
    try:
        from config import VECTOR_DB_DIR
        db_path = Path(VECTOR_DB_DIR)
    except ImportError:
        db_path = None
    
    # 如果包安装目录下有数据库，使用它；否则检查用户目录
    package_db_path = Path(__file__).parent.parent / "data" / "db"
    user_db_path = Path.home() / ".ise_agent" / "db"
    
    # 优先使用用户目录的数据库
    if user_db_path.exists() and list(user_db_path.iterdir()):
        actual_db_dir = str(user_db_path)
    elif package_db_path.exists() and list(package_db_path.iterdir()):
        actual_db_dir = str(package_db_path)
    elif db_path and db_path.exists() and list(db_path.iterdir()):
        actual_db_dir = str(db_path)
    else:
        actual_db_dir = None
    
    # 设置数据库路径
    if actual_db_dir:
        os.environ["VECTOR_DB_DIR"] = actual_db_dir
        # 临时修改 config 模块的变量
        try:
            import config as config_module
            config_module.VECTOR_DB_DIR = actual_db_dir
        except ImportError:
            pass
    else:
        # 如果没有找到数据库，尝试使用用户目录
        user_db_path.mkdir(parents=True, exist_ok=True)
        actual_db_dir = str(user_db_path)
        os.environ["VECTOR_DB_DIR"] = actual_db_dir
        try:
            import config as config_module
            config_module.VECTOR_DB_DIR = actual_db_dir
        except ImportError:
            pass
    
    v_manager = VectorManager()
    vectordb = v_manager.load_vector_db()
    init_end = time.time()
    
    if not vectordb:
        print(f"\n{YELLOW}[!] 未检测到知识库。{END}")
        print(f"{GREY}如果你是首次使用，请先构建知识库：{END}")
        print(f"{CYAN}  ise-agent build{END}")
        print(f"\n{GREY}或者，如果你有已构建的数据库，请将其放置在以下任一位置：{END}")
        print(f"  • {user_db_path}")
        print(f"  • {package_db_path}")
        return
    
    agent = CourseAssistantAgent(vector_db=vectordb)
    print(f"{GREY}(系统初始化耗时: {init_end - init_start:.2f} 秒){END}")
    print(f"{GREY}(当前使用模型: {config.get('llm_provider')}){END}")
    
    print("\n" + "="*50)
    print(f"{GREEN}同学你好呀，我是本节课的智能 AI 助教，随时欢迎提问~ {END}")
    print(f"{GREEN}我会先基于 ISE3309 回答，再针对 CS 系列进行资料上的补充~ {END}")
    print(f"{GREY}输入 quit/exit/退出 可以结束对话{END}")
    
    try:
        import readline
    except ImportError:
        pass
    
    while True:
        try:
            user_input = input("\n➲ [学生提问]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{GREY}再见！{END}")
            break
            
        if user_input.lower() in ['quit', 'exit', '退出']:
            print(f"\n{GREY}再见！{END}")
            break
        if not user_input:
            continue
            
        print(f"{GREY}助教正在深度思考中...{END}")
        try:
            answer, sources, metrics = agent.ask(user_input)
            
            parts = answer.split("\n\n【CS231n/224n/336 课程补充材料】")
            
            # --- 展示 ISE3309 部分 ---
            print(f"\n{BOLD}{GREEN}┏" + "━"*15 + " ISE3309 核心回答 " + "━"*15 + f"┓{END}")
            ise_content = parts[0].replace("【ISE3309 核心解答】", "").strip()
            print(render_styled_text(ise_content))
            
            # --- 展示 CS 进阶部分 ---
            if len(parts) > 1:
                print(f"\n{BOLD}{MAGENTA}┏" + "━"*15 + " CS 系列课程补充材料 " + "━"*15 + f"┓{END}")
                cs_content = parts[1].strip()
                print(render_styled_text(cs_content))
            
            # --- 展示 来源部分 ---
            print(f"\n{GREY}" + "—"*30)
            print(f"{BOLD}参考来源:{END}")
            for s in sources:
                styled_s = re.sub(r"(https?://[^\s\)]+)", f"{UNDERLINE}{BLUE}\\1{END}", s)
                print(f"  • {styled_s}")
            
            # --- 展示 性能指标 ---
            print(f"\n{GREY}⏱ 性能统计: 检索 {metrics['retrieval_time']:.2f}s | 生成 {metrics['generation_time']:.2f}s{END}")
            print(f"{GREY}" + "—"*50 + f"{END}")
        except Exception as e:
            print(f"\n{YELLOW}❌ 发生错误: {e}{END}")
            print(f"{GREY}请检查配置和网络连接。{END}")

if __name__ == "__main__":
    main()

