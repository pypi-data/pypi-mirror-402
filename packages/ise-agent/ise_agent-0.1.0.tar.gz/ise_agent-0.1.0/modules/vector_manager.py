import os
from uuid import uuid4
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from config import (
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    VECTOR_DB_DIR,
    EMBEDDING_PROVIDER,
    EMBEDDING_MODEL_NAME,
    HF_ENDPOINT,
)

class VectorManager:
    """管理文档切分、向量化和向量数据库存储"""

    def __init__(self):
        # 使用免费的 HuggingFace Embedding 模型
        if HF_ENDPOINT:
            os.environ["HF_ENDPOINT"] = HF_ENDPOINT

        self.embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL_NAME
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " "]
        )

    def process_and_store(self, documents):
        """对文档进行切分并存入向量数据库"""
        if not documents:
            return None
            
        chunks = self.text_splitter.split_documents(documents)
        
        # 创建或加载持久化的 Chroma 数据库，并分批写入（避免超过 Chroma 的最大 batch size）
        vectordb = Chroma(
            persist_directory=VECTOR_DB_DIR,
            embedding_function=self.embeddings
        )

        batch_size = 1000
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            ids = [str(uuid4()) for _ in batch]
            vectordb.add_documents(batch, ids=ids)
        vectordb.persist()
        return vectordb

    def load_vector_db(self):
        """加载已有的向量数据库"""
        if os.path.exists(VECTOR_DB_DIR) and os.listdir(VECTOR_DB_DIR):
            return Chroma(
                persist_directory=VECTOR_DB_DIR,
                embedding_function=self.embeddings
            )
        return None

