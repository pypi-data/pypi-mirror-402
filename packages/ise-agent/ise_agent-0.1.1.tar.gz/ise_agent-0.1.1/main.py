import os
import re
import time
try:
    import readline
except ImportError:
    pass

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

def main():
    suppress_noisy_logs()
    
    # 统计初始化时间
    init_start = time.time()
    print(f"\n{BOLD}{CYAN}=== 正在初始化 ISE3309 智能助教系统... ==={END}")
    
    v_manager = VectorManager()
    vectordb = v_manager.load_vector_db()
    init_end = time.time()

    if not vectordb:
        print(f"\n{YELLOW}[!] 未检测到知识库。请先运行 scripts/build_kb.py 构建向量库。{END}")
        return

    agent = CourseAssistantAgent(vector_db=vectordb)
    print(f"{GREY}(系统初始化耗时: {init_end - init_start:.2f} 秒){END}")
    
    print("\n" + "="*50)
    print(f"{GREEN}同学你好呀，我是本节课的智能 AI 助教，随时欢迎提问~ {END}")
    print(f"{GREEN}我会先基于 ISE3309 回答，再针对 CS 系列进行资料上的补充~ {END}")
    
    while True:
        try:
            user_input = input("\n➲ [学生提问]: ").strip()
        except EOFError:
            break
            
        if user_input.lower() in ['quit', 'exit', '退出']:
            break
        if not user_input:
            continue
            
        print(f"{GREY}助教正在深度思考中...{END}")
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


if __name__ == "__main__":
    main()
