# ISE3309 AI 课程助教系统

这是一个基于创新框架：级联式 RAG 架构的 AI 助教系统。
它首先基于 **ISE3309 《人工智能算法实践》** 的课程课件进行回答，并自动提取技术关键词去 **CS231n / CS224n / CS336** 等国外优秀人工智能课程资料中检索进阶内容进行补充。

我们将分三类用户进行使用讲解：
- **普通用户**（推荐）：只需一行命令安装，即可使用 → [快速开始](#-快速开始一键安装)
- **开发者**：想在此项目上进行延伸拓展或是想利用自己的资料搭建 AI 助教 → [开发者指南](#-开发者指南前置数据准备)
- **本地用户**：需要在本地环境手动设置 → [使用者指南](#-使用者指南运行说明)

---

## 🚀 快速开始（一键安装）

### 安装

```bash
pip install ise-agent
```

或者从 GitHub 源码安装：

```bash
git clone https://github.com/likelihood333/ISE3309-AI-Intelligent-Teaching-Assistant.git
cd ISE3309-AI-Intelligent-Teaching-Assistant
pip install -e .
```

### 首次运行

首次运行时会自动启动**交互式配置向导**，引导你完成设置：

```bash
ise-agent
```

配置向导会询问：
1. **选择大语言模型提供商**（通义千问、Gemini、OpenAI 兼容 API 或本地模型）
2. **输入 API Key**（根据选择的提供商）
3. **设置 HuggingFace 镜像站**（可选，用于加速模型下载）

配置会自动保存到 `~/.ise_agent_config.json`，下次运行时会自动加载。

### 构建知识库（首次使用必需）

如果你是首次使用，或者需要更新知识库：

```bash
ise-agent-build
```

这将：
- 扫描本地文档（`data/source/ISE3309/` 下的 PDF/Notebook）
- 抓取在线课程资料（从 `data/source/curated_links.txt`）
- 构建向量数据库

### 开始对话

配置完成后，直接运行：

```bash
ise-agent
```

即可开始与 AI 助教对话！

---

## 🛠 开发者指南 (前置数据准备)

如果您需要更新或添加课程资料，请遵循以下步骤：

### 1. 整理本地 PDF/Notebook
- 将 ISE3309 的讲义存放在 `/data/source/ISE3309/` 目录下。
- **章节识别规则**：系统会根据文件夹名称或文件名（如 `Lecture14`）自动识别章节。请确保路径中包含 `LectureXX` 关键字。
- **支持格式**：`.pdf` 和 `.ipynb`。

### 2. 更新在线课程链接
- 所有的在线课程（CS231n, CS224n, CS336）抓取清单统一维护在 `/data/source/curated_links.txt` 中。
- **文件格式**：
  ```text
  # CS224N
  https://example.com/slides1.pdf
  
  # CS336
  https://example.com/lecture1.json
  ```
- 系统会自动根据 `# 课程名` 注释对链接进行分组归类。

### 3. 构建/更新知识库
每次修改完本地文件或 `curated_links.txt` 后，**必须**重新运行构建脚本：
```bash
# 使用 uv 或你的虚拟环境 Python
python -m scripts.build_kb
```
- 该脚本会清空旧的向量数据库，重新解析所有 PDF/Notebook，并实时爬取在线链接。
- 构建完成后，终端会显示 **“总耗时”** 和各个课程的 **“文档块数量统计”**。

---

## 📖 使用者指南 (手动运行说明)

如果你不想通过 pip 安装，可以在本地直接运行：

### 1. 环境准备

使用 uv 工具安装虚拟环境：
```bash
pip install uv # 如果没有安装需执行
uv venv agent python==3.11
pip install -r requirements.txt
```

### 2. 配置 API Key

**方式一：环境变量（推荐）**
```bash
export QWEN_API_KEY="your-api-key"  # 使用千问
export LLM_PROVIDER="qwen"          # 或 "gemini", "openai_compatible", "local"
```

**方式二：修改 config.py**
直接在 `config.py` 中填入你的 API Key。

### 3. 运行 AI 助教系统
直接在根目录下运行：
```bash
python main.py
```

### 4. 系统特色
- **双段输出**：
  - **绿色框**：来自 ISE3309 的核心解答。
  - **紫色框**：来自顶级 CS 课程的技术原件摘录（对比进阶）。
- **性能透明**：每次回答下方都会显示 **“⏱ 性能统计”**，包括：
  - **检索耗时**：在向量库中寻找相关片段的时间。
  - **生成耗时**：大模型逻辑思考和组织语言的时间。

### 5. 退出问答
对话框中输入 `quit`、`exit` 或使用 `Ctrl+C` 即可。

---

## ⏱ 性能指标说明
系统会自动记录并打印以下环节的耗时：
1. **系统初始化**：加载向量库索引的时间（仅在 `main.py` 启动时）。
2. **检索耗时**：包括 Step 1（ISE3309）和 Step 3（CS 进阶）两次向量搜索的总和。
3. **生成耗时**：包括 Step 1（核心回答）、Step 2（关键词提取）和 Step 3（进阶回答）三次模型调用的总和。
