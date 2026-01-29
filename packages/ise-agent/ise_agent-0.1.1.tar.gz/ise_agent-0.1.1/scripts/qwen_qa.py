import os
import sys
import argparse

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# 允许用 `python scripts/qwen_qa.py` 直接运行（确保能 import config / modules）
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import (
    LOCAL_MODEL_NAME,
    LOCAL_MODEL_REVISION,
    DEVICE,
    TEMPERATURE,
    TOP_P,
    TOP_K,
    MAX_NEW_TOKENS,
)
from modules.noise import suppress_noisy_logs


def build_prompt(tokenizer, question: str) -> tuple[str, str]:
    """
    返回 (full_prompt, user_content)。
    若模型支持 chat template，则使用 chat 格式；否则使用纯文本 prompt。
    """
    system = "你是一个有帮助且诚实的中文助教。请直接回答问题。"
    user = question.strip()

    if hasattr(tokenizer, "apply_chat_template"):
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        full = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        return full, user

    # fallback: plain text
    full = f"{system}\n\n用户：{user}\n\n助手："
    return full, user


def generate_answer(model, tokenizer, question: str) -> str:
    prompt, _ = build_prompt(tokenizer, question)
    inputs = tokenizer(prompt, return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    do_sample = TEMPERATURE > 0
    out = model.generate(
        **inputs,
        max_new_tokens=MAX_NEW_TOKENS,
        temperature=TEMPERATURE if do_sample else 1.0,
        top_p=TOP_P,
        top_k=TOP_K,
        do_sample=do_sample,
        repetition_penalty=1.12,
        no_repeat_ngram_size=4,
        eos_token_id=tokenizer.eos_token_id,
    )
    text = tokenizer.decode(out[0], skip_special_tokens=True)
    answer = text[len(prompt):].strip()
    return answer


def main():
    suppress_noisy_logs()

    parser = argparse.ArgumentParser(description="直接调用 Qwen3-0.6B 进行问答（不使用知识库）")
    parser.add_argument("-q", "--question", type=str, default="", help="单次提问内容；为空则进入交互模式")
    args = parser.parse_args()

    model_kwargs = {"trust_remote_code": True}
    if LOCAL_MODEL_REVISION:
        model_kwargs["revision"] = LOCAL_MODEL_REVISION

    tokenizer = AutoTokenizer.from_pretrained(LOCAL_MODEL_NAME, **model_kwargs)
    model = AutoModelForCausalLM.from_pretrained(
        LOCAL_MODEL_NAME,
        torch_dtype="auto",
        device_map=DEVICE if DEVICE != "cpu" else None,
        **model_kwargs,
    )
    if DEVICE == "cpu":
        model = model.to("cpu")

    if args.question.strip():
        print(generate_answer(model, tokenizer, args.question))
        return

    print("=== Qwen 问答模式（输入 'quit' 退出） ===")
    while True:
        q = input("\n[你]: ").strip()
        if not q:
            continue
        if q.lower() in ("quit", "exit", "q", "退出"):
            break
        print("[Qwen]: ", end="", flush=True)
        print(generate_answer(model, tokenizer, q))


if __name__ == "__main__":
    main()

