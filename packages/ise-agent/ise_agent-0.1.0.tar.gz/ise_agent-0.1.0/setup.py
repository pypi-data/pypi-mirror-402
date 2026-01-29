from setuptools import setup, find_packages

setup(
    name="ai-course-tutor",
    version="0.1.0",
    description="人工智能算法实践课程智能助教",
    packages=find_packages(),
    py_modules=["main", "config"],
    install_requires=[
        "langchain>=0.2.0,<0.3.0",
        "langchain-community>=0.2.0,<0.3.0",
        "langchain-core>=0.2.0,<0.3.0",
        "langchain-huggingface",
        "chromadb",
        "pypdf",
        "nbformat",
        "beautifulsoup4",
        "requests",
        "sentence-transformers",
        "tabulate",
        "transformers",
        "torch",
        "peft",
        "accelerate",
        "datasets",
    ],
    entry_points={
        "console_scripts": [
            "ai-course-tutor=main:main",
        ]
    },
)

