from langchain.chains import RetrievalQA
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.vectorstores.base import VectorStoreRetriever
from langchain.schema import Document
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from typing import List, Dict, Any, Optional
import asyncio
import time
import re
import logging


class EnhancedRAGChain:
    """Enhanced RAG chain"""

    def __init__(self, model_name: str = "gpt-4o", temperature: float = 0.1):
        try:
            self.llm = ChatOpenAI(model_name=model_name, temperature=temperature)
            self.financial_keywords = self._load_financial_keywords()
        except Exception as e:
            logging.error(f"Error initializing EnhancedRAGChain: {e}")
            raise

    def _load_financial_keywords(self) -> Dict[str, List[str]]:
        """Load financial keywords"""
        try:
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
                ]
            }
        except Exception as e:
            logging.error(f"Error loading financial keywords: {e}")
            raise

    def build_smart_rag_chain(
            self,
            vectorstore: VectorStoreRetriever,
            query_type: str = "general"
    ) -> RetrievalQA:
        """Build smart RAG chain"""
        try:
            prompt_template = self._get_prompt_by_type(query_type)
            smart_retriever = self._create_smart_retriever(vectorstore)
            rag_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                retriever=smart_retriever,
                chain_type="stuff",
                chain_type_kwargs={"prompt": prompt_template},
                return_source_documents=True
            )
            return rag_chain
        except Exception as e:
            logging.error(f"Error building RAG chain: {e}")
            raise

    def _get_prompt_by_type(self, query_type: str) -> ChatPromptTemplate:
        """Get prompt by query type"""
        try:
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

            return ChatPromptTemplate.from_template(base_template + specific_instruction)
        except Exception as e:
            logging.error(f"Error generating prompt for query_type {query_type}: {e}")
            raise

    def _create_smart_retriever(self, vectorstore: VectorStoreRetriever) -> VectorStoreRetriever:
        """Create smart retriever (placeholder for custom retriever logic)"""
        return vectorstore  # 可扩展为更复杂的检索器