# integrated_rag.py
"""
整合后的RAG框架：基于rag_service.py，合并rag_chain_enhanced.py的提示词逻辑和pdf_processor.py的PDF处理。
针对金融10-K文档的风险分析优化，支持PDF上传、长文档分割、嵌入、检索和生成。
"""

import asyncio
import json
import time
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime
import re
from collections import Counter, defaultdict
from dotenv import load_dotenv
import os
import logging

# LangChain imports
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document
from langchain.retrievers import (
    BM25Retriever,
    EnsembleRetriever,
    ContextualCompressionRetriever,
    MultiQueryRetriever
)
from langchain.retrievers.document_compressors import (
    LLMChainExtractor,
    EmbeddingsFilter,
    DocumentCompressorPipeline
)
from langchain.chains import LLMChain
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

# NLP and ML imports
import spacy
try:
    import sentence_transformers
    from sentence_transformers import SentenceTransformer, util
except ImportError:
    sentence_transformers = None
from pathlib import Path

# 加载 .env 文件
load_dotenv()

# 配置类（从原RAGConfig中提取，默认值优化为长文档）
class RAGConfig:
    LLM_MODEL = "gpt-4o"
    LLM_TEMPERATURE = 0.1
    MAX_TOKENS = 2000
    CHUNK_SIZE = 1500  # 优化为长10-K文档
    CHUNK_OVERLAP = 300
    RETRIEVAL_K = 10  # 默认检索Top-10
    RERANK_TOP_K = 5
    SIMILARITY_THRESHOLD = 0.7
    USE_RERANKING = True
    USE_COMPRESSION = True
    ENABLE_MULTI_QUERY = True
    SENTENCE_MODEL = "all-MiniLM-L6-v2"  # 用于语义相似度

class IntegratedRAGService:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = {**RAGConfig.__dict__, **(config or {})}
        self.llm = ChatOpenAI(
            model=self.config["LLM_MODEL"],
            api_key=os.getenv("OPENAI_API_KEY", ""),
            temperature=self.config["LLM_TEMPERATURE"],
            max_tokens=self.config["MAX_TOKENS"]
        )
        self.embedding_model = OpenAIEmbeddings(
            api_key=os.getenv("OPENAI_API_KEY", "")
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config["CHUNK_SIZE"],
            chunk_overlap=self.config["CHUNK_OVERLAP"],
            separators=["\n\n", "\n", ". ", "。", "；", ";", ":", "：", " "]
        )
        self.nlp = spacy.load("en_core_web_sm") if spacy else None
        self.sentence_model = SentenceTransformer(RAGConfig.SENTENCE_MODEL) if sentence_transformers else None
        self.financial_keywords = self._load_financial_keywords()
        self.risk_entities = self._load_risk_entities()
        self.vectorstore_cache = {}
        self.query_cache = {}
        self.risk_keywords = ["risk", "uncertainty", "threat", "challenge", "exposure"]  # 从pdf_processor整合

    def _load_financial_keywords(self) -> Dict[str, List[str]]:
        """加载金融关键词词典（从原文件整合）"""
        return {
            "risk_types": [
                "market risk", "credit risk", "operational risk", "liquidity risk",
                "regulatory risk", "reputational risk", "cybersecurity risk"
            ],
            "regulations": [
                "SOX", "SEC", "FINRA", "Basel", "Dodd-Frank", "GAAP", "IFRS"
            ],
            "financial_metrics": [
                "VaR", "leverage ratio", "capital ratio", "ROE", "ROA", "debt to equity"
            ],
            "risk_indicators": ["loss", "decline", "negative", "adverse", "concern"],
            "financial_statements": ["balance sheet", "income statement", "cash flow"]
        }

    def _load_risk_entities(self) -> Dict[str, Any]:
        """加载风险实体模式（从原文件整合）"""
        return {
            "monetary_patterns": [r'\$\d+(?:\.\d+)?(?:[KMGB])?'],
            "percentage_patterns": [r'\d+(?:\.\d+)?%'],
            "date_patterns": [r'\d{4}-\d{2}-\d{2}'],
            "risk_severity_patterns": [r'(high|medium|low)\s+risk']
        }

    async def process_pdf(self, file_path: str, document_id: str, metadata: dict) -> dict:
        """PDF处理（整合自pdf_processor.py）"""
        try:
            start_time = time.time()
            loader = PyPDFLoader(file_path)
            pages = await loader.aload()
            logging.info(f"Loaded {len(pages)} pages from {file_path} in {time.time() - start_time:.2f}s")
            paragraphs = []
            for page in pages:
                chunks = self.text_splitter.split_text(page.page_content)
                section_name = self._identify_section(page.page_content) or metadata.get("section", "general")
                for chunk in chunks:
                    if any(keyword.lower() in chunk.lower() for keyword in self.risk_keywords):
                        paragraphs.append({
                            "content": chunk,
                            "metadata": {
                                **metadata,
                                "page": page.metadata.get("page", 0),
                                "section_name": section_name
                            }
                        })
            logging.info(f"Processed {len(paragraphs)} chunks for document {document_id}")
            storage_path = Path("storage") / f"{document_id}.json"
            storage_path.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(storage_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps({"paragraphs": paragraphs, "metadata": metadata}, indent=2, ensure_ascii=False))
            logging.info(f"Completed processing {file_path} in {time.time() - start_time:.2f}s")
            return {"document_id": document_id, "paragraphs": paragraphs}
        except FileNotFoundError as e:
            logging.error(f"PDF file not found: {file_path}, error: {e}")
            raise
        except Exception as e:
            logging.error(f"Error processing PDF {file_path}: {e}")
            raise

    def _identify_section(self, content: str) -> Optional[str]:
        """识别章节（整合自pdf_processor.py和rag_service.py）"""
        section_patterns = [
            r'Item\s+1A\.?\s+Risk Factors',
            r'Management’s Discussion and Analysis',
            r'Financial Statements',
            r'Item\s+8\.?\s+Financial Statements',
            r'Item\s+\d+[A-Z]?\.\s+([^\.]+)', r'PART\s+[IVX]+\s*[-–]?\s*([^\.]+)'
        ]
        for pattern in section_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        return None

    async def build_enhanced_vectorstore(self, documents: List[str], document_metadata: List[Dict[str, Any]], save_path: Optional[str] = None) -> FAISS:
        """构建增强向量数据库（原rag_service.py核心）"""
        print("🔄 开始构建增强向量数据库...")
        processed_docs = await self._preprocess_documents(documents, document_metadata)
        chunks = await self._intelligent_chunking(processed_docs)
        enhanced_chunks = await self._enhance_chunks_with_entities(chunks)
        vectorstore = await asyncio.to_thread(
            FAISS.from_texts,
            [chunk["content"] for chunk in enhanced_chunks],
            self.embedding_model,
            metadatas=[chunk["metadata"] for chunk in enhanced_chunks]
        )
        if save_path:
            await asyncio.to_thread(vectorstore.save_local, save_path, index_compression="lz4")
            metadata_path = f"{save_path}_metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump({"chunks": enhanced_chunks, "build_time": datetime.now().isoformat(), "config": self.config}, f, ensure_ascii=False, indent=2)
        print(f"✅ 向量数据库构建完成，包含 {len(enhanced_chunks)} 个增强块")
        return vectorstore

    # 以下是原rag_service.py的其他方法，略微简化以避免冗长
    # （包括_preprocess_documents, _clean_text, _identify_document_sections, _extract_key_information, _intelligent_chunking, _semantic_chunking, _analyze_chunk_semantics, _classify_chunk_type, _calculate_importance_score, _enhance_chunks_with_entities, _annotate_entities, _generate_chunk_summary, _extract_chunk_keywords, advanced_retrieve, _enhance_query, _get_financial_synonyms, _generate_multi_perspective_queries, _extract_query_entities, _expand_with_entities, _hybrid_retrieval, _keyword_filter, _deduplicate_documents, _intelligent_reranking, _calculate_rerank_score, _compress_context）

    # 从rag_chain_enhanced.py整合提示词逻辑
    def _get_prompt_by_type(self, query_type: str) -> str:
        """生成提示词模板（整合自rag_chain_enhanced.py）"""
        base_template = """
        您是一位资深金融风险分析专家，请基于提供的10-K文档内容回答用户问题。

        文档内容：
        {context}

        用户问题：
        {question}

        """
        if query_type == "risk":
            specific_instruction = """
            回答要求：
            - 重点识别和分析各类风险（市场、信用、操作、流动性等）
            - 评估风险严重程度（1-5级）和潜在影响
            - 引用具体的风险数据和指标
            - 提及相关的风险缓解措施
            - 如果涉及监管风险，请明确相关法规
            """
        elif query_type == "financial":
            specific_instruction = """
            回答要求：
            - 提供具体的财务数据和指标
            - 分析财务趋势和变化原因
            - 评估对公司财务健康状况的影响
            """
        else:
            specific_instruction = """
            回答要求：
            - 提供准确、具体的回答
            - 引用相关文档内容
            - 如信息不足，明确说明
            """
        return base_template + specific_instruction

    async def _generate_dynamic_prompt(self, query: str, documents: List[Document]) -> ChatPromptTemplate:
        """动态提示词生成（结合原逻辑和rag_chain_enhanced.py）"""
        query_type = self._classify_query_type(query)
        template = self._get_prompt_by_type(query_type)  # 使用整合的提示词
        return ChatPromptTemplate.from_template(template)

    # 原intelligent_qa、_preprocess_query等方法保持不变

    # 测试函数
    async def test_integrated_rag(pdf_path: str = None):
        """测试整合后的RAG"""
        rag_service = IntegratedRAGService()
        if pdf_path:
            # 先处理PDF
            metadata = {"document_type": "10-K", "company_name": "TestCorp"}
            processed = await rag_service.process_pdf(pdf_path, "test_doc", metadata)
            documents = [p["content"] for p in processed["paragraphs"]]
            document_metadata = [p["metadata"] for p in processed["paragraphs"]]
        else:
            # 默认测试文档
            documents = [
                "公司面临的主要风险包括市场风险、信用风险和操作风险。市场风险主要来自利率变化和汇率波动，预计可能导致年度收益下降5-10%。",
                "根据SOX 404条款要求，公司建立了内部控制制度。但在2023年度审计中发现了一项重大缺陷，涉及收入确认流程。",
                "公司的流动性比率为1.5，债务权益比为0.8。现金流量表显示经营活动现金流为正，但投资活动现金流为负。"
            ]
            document_metadata = [{"document_type": "10-K", "section": "Risk Factors"}, {"document_type": "10-K", "section": "Internal Controls"}, {"document_type": "10-K", "section": "Financial Statements"}]
        print("🔄 构建向量数据库...")
        vectorstore = await rag_service.build_enhanced_vectorstore(documents, document_metadata, save_path="test_vectorstore")
        test_queries = ["公司面临哪些主要风险？", "SOX合规状况如何？", "公司的财务状况是否健康？", "市场风险对公司的影响有多大？"]
        for query in test_queries:
            print(f"\n🔍 测试查询：{query}")
            result = await rag_service.intelligent_qa(query, vectorstore)
            print(f"答案：{result['answer']}")
            print(f"置信度：{result['confidence_score']:.2f}")
            print(f"检索文档数：{result['documents_retrieved']}")
            print(f"处理时间：{result['processing_time']:.2f}秒")

if __name__ == "__main__":
    asyncio.run(test_integrated_rag(pdf_path="./data/10k.pdf"))  # 替换为你的PDF路径
