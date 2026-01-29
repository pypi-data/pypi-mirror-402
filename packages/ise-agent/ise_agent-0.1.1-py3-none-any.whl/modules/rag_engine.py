import torch
import re
import time
from collections import defaultdict
from transformers import AutoModelForCausalLM, AutoTokenizer
from config import (
    LOCAL_MODEL_NAME,
    LOCAL_MODEL_REVISION,
    DEVICE,
    TEMPERATURE,
    TOP_P,
    TOP_K,
    MAX_NEW_TOKENS,
    RETRIEVAL_K,
    RAG_MODE,
    LLM_PROVIDER,
    GEMINI_API_KEY,
    GEMINI_MODEL_NAME,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL_NAME,
    QWEN_API_KEY,
    QWEN_MODEL_NAME,
)

class CourseAssistantAgent:
    """级联 RAG 框架：ISE3309 基础回答 + CS 系列课程原件摘录"""

    def __init__(self, vector_db):
        self.vector_db = vector_db
        self.provider = LLM_PROVIDER.lower()
        
        if self.provider == "local":
            self._init_local_model()
        elif self.provider == "gemini":
            self._init_gemini()
        elif self.provider == "qwen":
            self._init_qwen()
        elif self.provider == "openai_compatible":
            self._init_openai()
        
        self.prompt_stage1 = """你是《ISE3309》课程助教。请根据【ISE3309 背景资料】回答问题。
要求：
1. 聚焦于 ISE3309 讲义中的核心定义和方法。
2. 保持回答的完整性。

[ISE3309 背景资料]
{context}

[问题]
{question}

[回答]
"""

        self.prompt_stage2 = """你现在是进阶学术导师。
请从【CS 进阶背景资料】中，精准提取出能深化理解刚才问题的“技术原件片段 (Technical Snippets)”。

要求：
1. **原汁原味**：尽可能保留资料中的核心原句、英文定义、关键参数或算法步骤。
2. **精简修饰**：AI 可以对过于冗长的上下文进行微调或省略，但严禁改变技术原意。
3. **排版格式**：请按以下格式列出 2-3 个最具代表性的对比/进阶片段：
   > 课程名 (来源链接/文件): [原片段内容...]
4. **拒绝重复**：如果资料内容与 ISE3309 完全一样，请略过。

[ISE3309 回答]
{output1}

[CS 进阶背景资料]
{context}

[CS 课程进阶原件摘录]
"""

    def _init_local_model(self):
        model_kwargs = {"trust_remote_code": True}
        if LOCAL_MODEL_REVISION: model_kwargs["revision"] = LOCAL_MODEL_REVISION
        self.tokenizer = AutoTokenizer.from_pretrained(LOCAL_MODEL_NAME, **model_kwargs)
        self.model = AutoModelForCausalLM.from_pretrained(
            LOCAL_MODEL_NAME, torch_dtype="auto",
            device_map=DEVICE if DEVICE != "cpu" else None, **model_kwargs
        )
        if DEVICE == "cpu": self.model = self.model.to("cpu")

    def _init_gemini(self):
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(GEMINI_MODEL_NAME)

    def _init_qwen(self):
        from openai import OpenAI
        self.client = OpenAI(api_key=QWEN_API_KEY, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.api_model_name = QWEN_MODEL_NAME

    def _init_openai(self):
        from openai import OpenAI
        self.client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        self.api_model_name = OPENAI_MODEL_NAME

    def _generate(self, prompt: str) -> str:
        if self.provider == "local":
            inputs = self.tokenizer(prompt, return_tensors="pt")
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            outputs = self.model.generate(
                **inputs, max_new_tokens=MAX_NEW_TOKENS, temperature=TEMPERATURE,
                repetition_penalty=1.12, no_repeat_ngram_size=4,
                eos_token_id=self.tokenizer.eos_token_id,
            )
            return self.tokenizer.decode(outputs[0], skip_special_tokens=True)[len(prompt):].strip()
        elif self.provider == "gemini":
            try: return self.model.generate_content(prompt).text
            except Exception as e: return f"Gemini 错误: {e}"
        elif self.provider in ["qwen", "openai_compatible"]:
            try:
                res = self.client.chat.completions.create(
                    model=self.api_model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=TEMPERATURE, max_tokens=MAX_NEW_TOKENS,
                )
                return res.choices[0].message.content
            except Exception as e: return f"API 错误: {e}"
        return "Unknown Provider"

    def _extract_keywords(self, text: str) -> list[str]:
        prompt = f"""从以下文本中提取 3 个核心技术术语。只返回关键词，逗号隔开。
[文本]
{text}
[关键词]"""
        raw = self._generate(prompt)
        keywords = [k.strip() for k in re.split(r"[,，、\n]", raw) if k.strip()]
        stop_words = {"lecture", "homework", "assignment", "ise3309", "cs336", "cs231n", "cs224n", "助教"}
        return [k for k in keywords if k.lower() not in stop_words][:3]

    def _infer_course_from_source(self, source: str) -> str:
        if not source: return "Unknown"
        m = re.search(r"(?:Web|Local)_(?:PDF|JSON|Notebook|Course):\s*([A-Za-z0-9]+)", source)
        if m: return m.group(1).upper()
        for c in ["CS231N", "CS224N", "CS336", "ISE3309"]:
            if c in source.upper(): return c
        return "General"

    def ask(self, query):
        metrics = {"retrieval_time": 0.0, "generation_time": 0.0}
        if not self.vector_db: return "向量数据库未初始化。", [], metrics

        # --- 阶段 1: ISE3309 ---
        chapter_filter = None
        m = re.search(r"lecture\s*(\d+)", query, re.IGNORECASE)
        if m: chapter_filter = {"chapter": f"Lecture{int(m.group(1))}"}

        print(f"\n\033[94m[Step 1] 检索 ISE3309 核心资料...\033[0m")
        search_filter = {"course": "ISE3309"}
        if chapter_filter: search_filter = {"$and": [{"course": "ISE3309"}, chapter_filter]}

        t0 = time.time()
        ise_docs = self.vector_db.similarity_search(query, k=8, filter=search_filter)
        metrics["retrieval_time"] += (time.time() - t0)

        context1 = "\n\n".join([f"资料[{i+1}]: {d.page_content}" for i, d in enumerate(ise_docs)])
        
        t1 = time.time()
        output1 = self._generate(self.prompt_stage1.format(context=context1, question=query))
        metrics["generation_time"] += (time.time() - t1)
        
        # --- 阶段 2: 关键词 ---
        print(f"\033[94m[Step 2] 提取对标关键词...\033[0m")
        keywords_t = time.time()
        keywords = self._extract_keywords(output1)
        metrics["generation_time"] += (time.time() - keywords_t) # 关键词提取也算作模型生成耗时
        
        if not keywords: keywords = [query]
        print(f"    \033[90m核心点: {', '.join(keywords)}\033[0m")

        # --- 阶段 3: CS 进阶 ---
        print(f"\033[94m[Step 3] 检索 CS 进阶资料...\033[0m")
        t2 = time.time()
        cs_docs = self.vector_db.similarity_search(
            " ".join(keywords), k=5, 
            filter={"course": {"$in": ["CS231N", "CS224N", "CS336"]}}
        )
        metrics["retrieval_time"] += (time.time() - t2)
        
        context2_list = []
        for i, d in enumerate(cs_docs):
            c_name = d.metadata.get('course', 'Unknown')
            s_name = d.metadata.get('source', 'Unknown')
            context2_list.append(f"资料[{i+1}] (课程: {c_name}, 来源: {s_name}):\n{d.page_content}")
        
        context2 = "\n\n".join(context2_list)
        
        t3 = time.time()
        output2 = self._generate(self.prompt_stage2.format(output1=output1, context=context2))
        metrics["generation_time"] += (time.time() - t3)

        final_answer = f"【ISE3309 核心解答】\n{output1}\n\n"
        final_answer += f"【CS231n/224n/336 课程补充材料】\n{output2}"
        
        all_sources = sorted(list(set([d.metadata.get("source", "未知") for d in ise_docs + cs_docs])))
        return final_answer, all_sources, metrics

    @staticmethod
    def _dedupe_repetition(text: str) -> str:
        if not text: return text
        parts = re.split(r"(?<=[。！？!\\?])\s*", text)
        out = []
        for p in parts:
            if not p.strip(): continue
            if out and out[-1] == p.strip(): continue
            out.append(p.strip())
        return " ".join(out).strip()
