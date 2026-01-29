import os
import argparse
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments
from peft import LoraConfig, get_peft_model, TaskType


def build_prompt(instruction, input_text):
    if input_text:
        return f"指令：{instruction}\n输入：{input_text}\n回答："
    return f"指令：{instruction}\n回答："


def tokenize_function(examples, tokenizer, max_length):
    prompts = [
        build_prompt(inst, inp)
        for inst, inp in zip(examples["instruction"], examples.get("input", [""] * len(examples["instruction"])))
    ]
    outputs = examples["output"]
    texts = [p + o for p, o in zip(prompts, outputs)]
    tokenized = tokenizer(
        texts,
        truncation=True,
        max_length=max_length,
        padding="max_length",
    )
    tokenized["labels"] = tokenized["input_ids"].copy()
    return tokenized


def main():
    parser = argparse.ArgumentParser(description="Qwen 本地 LoRA 微调脚本")
    parser.add_argument("--model_name", default=os.getenv("LOCAL_MODEL_NAME", "Qwen/Qwen3-0.6B"))
    parser.add_argument("--train_file", default="data/finetune/train.jsonl")
    parser.add_argument("--output_dir", default="outputs/lora_qwen")
    parser.add_argument("--max_length", type=int, default=1024)
    parser.add_argument("--batch_size", type=int, default=2)
    parser.add_argument("--num_epochs", type=int, default=3)
    parser.add_argument("--lr", type=float, default=2e-4)
    args = parser.parse_args()

    tokenizer = AutoTokenizer.from_pretrained(args.model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model_name,
        torch_dtype="auto",
        device_map="auto",
        trust_remote_code=True,
    )

    # LoRA 配置（可对比实验的关键参数）
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=8,                 # 低秩维度，可尝试 4/8/16
        lora_alpha=16,       # 缩放系数
        lora_dropout=0.05,   # Dropout，避免过拟合
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],  # 可对比替换
    )
    model = get_peft_model(model, lora_config)

    dataset = load_dataset("json", data_files={"train": args.train_file})
    tokenized = dataset["train"].map(
        lambda x: tokenize_function(x, tokenizer, args.max_length),
        batched=True,
        remove_columns=dataset["train"].column_names,
    )

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=args.batch_size,
        num_train_epochs=args.num_epochs,
        learning_rate=args.lr,
        logging_steps=20,
        save_steps=200,
        save_total_limit=2,
        fp16=True,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized,
    )

    trainer.train()
    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)


if __name__ == "__main__":
    main()

