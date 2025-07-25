# utils/rag_config.py
from typing import Dict, Any
from dotenv import load_dotenv
import os

load_dotenv()

class RAGConfig:
    """RAG配置类"""
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    LLM_MODEL: str = "gpt-4o"
    SENTENCE_MODEL: str = "all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    RETRIEVAL_K: int = 10
    RERANK_TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.7
    USE_COMPRESSION: bool = True
    USE_RERANKING: bool = True
    ENABLE_MULTI_QUERY: bool = True
    CACHE_ENABLED: bool = True
    LLM_TEMPERATURE: float = 0.1
    MAX_TOKENS: int = 1000
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """获取配置字典"""
        return {
            "embedding_model": cls.EMBEDDING_MODEL,
            "llm_model": cls.LLM_MODEL,
            "sentence_model": cls.SENTENCE_MODEL,
            "chunk_size": cls.CHUNK_SIZE,
            "chunk_overlap": cls.CHUNK_OVERLAP,
            "retrieval_k": cls.RETRIEVAL_K,
            "rerank_top_k": cls.RERANK_TOP_K,
            "similarity_threshold": cls.SIMILARITY_THRESHOLD,
            "use_compression": cls.USE_COMPRESSION,
            "use_reranking": cls.USE_RERANKING,
            "enable_multi_query": cls.ENABLE_MULTI_QUERY,
            "cache_enabled": cls.CACHE_ENABLED,
            "llm_temperature": cls.LLM_TEMPERATURE,
            "max_tokens": cls.MAX_TOKENS,
            "openai_api_key": cls.OPENAI_API_KEY
        }