# services/rag_service.py
"""
统一的RAG服务 - 整合EnhancedRAGChain和AdvancedRAGService
针对金融风险分析优化的检索增强生成系统
"""

import asyncio
import json
import time
import os
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime
from collections import Counter, defaultdict

# LangChain imports
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from langchain.chains import RetrievalQA

# NLP imports
try:
    import spacy
    nlp_available = True
except ImportError:
    spacy = None
    nlp_available = False

try:
    from sentence_transformers import SentenceTransformer, util
    sentence_transformers_available = True
except ImportError:
    sentence_transformers_available = False

import re
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class UnifiedRAGService:
    """统一的RAG服务，整合简单和高级功能"""
    
    def __init__(self, config: Dict[str, Any] = None):
        # 默认配置
        self.config = {
            "chunk_size": 1000,
            "chunk_overlap": 200,
            "llm_temperature": 0.1,
            "max_tokens": 2000,
            "retrieval_k": 10,
            "rerank_top_k": 5,
            "similarity_threshold": 0.7,
            "use_reranking": True,
            "use_compression": True,
            "enable_multi_query": True,
            "model_name": "gpt-4o"
        }
        
        # 合并自定义配置
        if config:
            self.config.update(config)
        
        # 初始化LLM
        self.llm = ChatOpenAI(
            model=self.config["model_name"],
            api_key=os.getenv("OPENAI_API_KEY", ""),
            temperature=self.config["llm_temperature"],
            max_tokens=self.config["max_tokens"]
        )
        
        # 初始化embedding模型
        self.embedding_model = OpenAIEmbeddings(
            api_key=os.getenv("OPENAI_API_KEY", "")
        )
        
        # 初始化文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config["chunk_size"],
            chunk_overlap=self.config["chunk_overlap"],
            separators=["\n\n", "\n", ". ", "。", "；", ";", ":", "：", " "]
        )
        
        # 初始化NLP工具（如果可用）
        self.nlp = None
        if nlp_available:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except Exception as e:
                logging.warning(f"无法加载spacy模型: {e}")
        
        # 初始化sentence transformer（如果可用）
        self.sentence_model = None
        if sentence_transformers_available:
            try:
                self.sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception as e:
                logging.warning(f"无法加载sentence transformer: {e}")
        
        # 加载金融关键词和实体模式
        self.financial_keywords = self._load_financial_keywords()
        self.risk_entities = self._load_risk_entities()
        
        # 缓存
        self.vectorstore_cache = {}
        self.query_cache = {}

    def _load_financial_keywords(self) -> Dict[str, List[str]]:
        """加载金融关键词词典"""
        return {
            "risk_types": [
                "market risk", "credit risk", "operational risk", "liquidity risk",
                "regulatory risk", "reputational risk", "cybersecurity risk",
                "interest rate risk", "currency risk", "commodity risk"
            ],
            "regulations": [
                "SOX", "SEC", "FINRA", "Basel", "Dodd-Frank", "GAAP", "IFRS",
                "COSO", "PCAOB", "FDIC", "OCC"
            ],
            "financial_metrics": [
                "VaR", "leverage ratio", "capital ratio", "ROE", "ROA", "debt to equity",
                "current ratio", "quick ratio", "gross margin", "net margin", "EBITDA"
            ],
            "risk_indicators": [
                "risk", "uncertainty", "threat", "challenge", "exposure", "vulnerability",
                "adverse", "negative", "decline", "loss", "deficit", "concern", "issue"
            ],
            "financial_statements": [
                "balance sheet", "income statement", "cash flow statement", "statement of equity",
                "10-K", "10-Q", "8-K", "annual report", "quarterly report"
            ]
        }

    def _load_risk_entities(self) -> Dict[str, Any]:
        """加载风险实体识别模式"""
        return {
            "monetary_patterns": [
                r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|thousand|M|B|K))?',
                r'(?:USD|dollars?)\s*[\d,]+(?:\.\d{2})?',
                r'[\d,]+(?:\.\d{2})?\s*(?:million|billion|thousand)\s*(?:dollars?|USD)?'
            ],
            "percentage_patterns": [
                r'\d+(?:\.\d+)?%',
                r'\d+(?:\.\d+)?\s*percent',
                r'percentage\s*of\s*\d+(?:\.\d+)?'
            ],
            "date_patterns": [
                r'\d{4}',  # 年份
                r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s*\d{1,2},?\s*\d{4}',
                r'\d{1,2}/\d{1,2}/\d{4}',
                r'\d{4}-\d{2}-\d{2}'
            ],
            "risk_severity_patterns": [
                r'(?:high|medium|low|significant|material|substantial)\s*(?:risk|exposure|threat)',
                r'(?:critical|severe|moderate|minor)\s*(?:risk|impact|concern)'
            ]
        }

    async def build_enhanced_vectorstore(
        self, 
        documents: List[str], 
        document_metadata: List[Dict[str, Any]], 
        save_path: Optional[str] = None
    ) -> FAISS:
        """构建增强的向量数据库"""
        logging.info("🔄 开始构建增强向量数据库...")
        
        try:
            # 预处理文档
            processed_docs = await self._preprocess_documents(documents, document_metadata)
            
            # 智能分块
            chunks = await self._intelligent_chunking(processed_docs)
            
            # 增强chunks
            enhanced_chunks = await self._enhance_chunks_with_entities(chunks)
            
            # 构建向量数据库
            vectorstore = await asyncio.to_thread(
                FAISS.from_texts,
                [chunk["content"] for chunk in enhanced_chunks],
                self.embedding_model,
                metadatas=[chunk["metadata"] for chunk in enhanced_chunks]
            )
            
            # 保存到本地（如果指定了路径）
            if save_path:
                await asyncio.to_thread(vectorstore.save_local, save_path)
                
                # 保存元数据
                metadata_path = f"{save_path}_metadata.json"
                metadata_info = {
                    "chunks": enhanced_chunks,
                    "build_time": datetime.now().isoformat(),
                    "config": self.config,
                    "total_chunks": len(enhanced_chunks),
                    "documents_count": len(documents)
                }
                
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata_info, f, ensure_ascii=False, indent=2)
            
            logging.info(f"✅ 向量数据库构建完成，包含 {len(enhanced_chunks)} 个增强块")
            return vectorstore
            
        except Exception as e:
            logging.error(f"构建向量数据库失败: {e}")
            raise

    async def _preprocess_documents(self, documents: List[str], metadata: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """智能文档预处理"""
        processed = []
        
        for i, (doc, meta) in enumerate(zip(documents, metadata)):
            # 清理文本
            cleaned_text = self._clean_text(doc)
            
            # 识别文档段落
            sections = self._identify_document_sections(cleaned_text)
            
            # 提取关键信息
            key_info = self._extract_key_information(cleaned_text)
            
            processed_doc = {
                "content": cleaned_text,
                "metadata": {
                    **meta,
                    "sections": sections,
                    "key_info": key_info,
                    "document_index": i,
                    "processed_at": datetime.now().isoformat(),
                    "word_count": len(cleaned_text.split())
                }
            }
            processed.append(processed_doc)
        
        return processed

    def _clean_text(self, text: str) -> str:
        """文本清理"""
        # 标准化空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 标准化引号
        text = text.replace('"', '"').replace('"', '"').replace(''', "'").replace(''', "'")
        
        # 移除页码
        text = re.sub(r'Page \d+ of \d+', '', text)
        text = re.sub(r'\d+\s*$', '', text, flags=re.MULTILINE)
        
        # 修正常见OCR错误
        text = text.replace('l0', '10').replace('O0', '00')
        
        return text.strip()

    def _identify_document_sections(self, text: str) -> List[str]:
        """识别文档章节"""
        sections = []
        
        # 定义章节识别模式
        section_patterns = [
            r'Item\s+\d+[A-Z]?\.\s+([^\.]{10,100})',  # SEC Item sections
            r'PART\s+[IVX]+\s*[-–]?\s*([^\.]{10,100})',  # Part sections
            r'(?:^|\n)\s*(\d+\.\s+[^\.]{10,100})',  # Numbered sections
            r'(?:^|\n)\s*([A-Z][A-Z\s]{10,50})\s*(?:\n|$)'  # All caps headers
        ]
        
        for pattern in section_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            sections.extend([match.strip() for match in matches if len(match.strip()) > 5])
        
        # 去重并限制数量
        return list(set(sections))[:15]

    def _extract_key_information(self, text: str) -> Dict[str, Any]:
        """提取关键信息"""
        key_info = {
            "monetary_amounts": [],
            "percentages": [],
            "dates": [],
            "risk_mentions": [],
            "regulatory_references": []
        }
        
        # 提取货币金额
        for pattern in self.risk_entities["monetary_patterns"]:
            matches = re.findall(pattern, text, re.IGNORECASE)
            key_info["monetary_amounts"].extend(matches[:10])
        
        # 提取百分比
        for pattern in self.risk_entities["percentage_patterns"]:
            matches = re.findall(pattern, text, re.IGNORECASE)
            key_info["percentages"].extend(matches[:15])
        
        # 提取日期
        for pattern in self.risk_entities["date_patterns"]:
            matches = re.findall(pattern, text)
            key_info["dates"].extend(matches[:10])
        
        # 识别风险类型
        text_lower = text.lower()
        for risk_type in self.financial_keywords["risk_types"]:
            if risk_type in text_lower:
                key_info["risk_mentions"].append(risk_type)
        
        # 识别监管引用
        for regulation in self.financial_keywords["regulations"]:
            if regulation.lower() in text_lower:
                key_info["regulatory_references"].append(regulation)
        
        return key_info

    async def _intelligent_chunking(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """智能分块策略"""
        all_chunks = []
        
        for doc in documents:
            content = doc["content"]
            metadata = doc["metadata"]
            
            # 基础分块
            base_chunks = self.text_splitter.split_text(content)
            
            # 语义增强分块
            semantic_chunks = await self._semantic_chunking(base_chunks, metadata)
            all_chunks.extend(semantic_chunks)
        
        return all_chunks

    async def _semantic_chunking(self, chunks: List[str], base_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """基于语义的智能分块"""
        enhanced_chunks = []
        
        for i, chunk in enumerate(chunks):
            # 分析语义特征
            semantic_features = await self._analyze_chunk_semantics(chunk)
            
            # 分类chunk类型
            chunk_type = self._classify_chunk_type(chunk, semantic_features)
            
            # 计算重要性分数
            importance_score = self._calculate_importance_score(chunk, semantic_features)
            
            enhanced_chunk = {
                "content": chunk,
                "metadata": {
                    **base_metadata,
                    "chunk_index": i,
                    "chunk_type": chunk_type,
                    "importance_score": importance_score,
                    "semantic_features": semantic_features,
                    "word_count": len(chunk.split()),
                    "has_numbers": bool(re.search(r'\d', chunk)),
                    "has_risk_keywords": any(
                        keyword in chunk.lower() 
                        for keyword_list in self.financial_keywords.values() 
                        for keyword in keyword_list
                    )
                }
            }
            enhanced_chunks.append(enhanced_chunk)
        
        return enhanced_chunks

    async def _analyze_chunk_semantics(self, chunk: str) -> Dict[str, Any]:
        """分析chunk的语义特征"""
        features = {
            "entities": [],
            "risk_signals": 0,
            "financial_terms": 0,
            "regulatory_mentions": 0,
            "sentiment_indicators": []
        }
        
        # 使用spacy提取实体（如果可用）
        if self.nlp:
            try:
                doc = self.nlp(chunk)
                features["entities"] = [
                    {"text": ent.text, "label": ent.label_} 
                    for ent in doc.ents 
                    if ent.label_ in ["ORG", "MONEY", "PERCENT", "DATE", "LAW", "PERSON"]
                ]
            except Exception as e:
                logging.warning(f"实体提取失败: {e}")
        
        chunk_lower = chunk.lower()
        
        # 计算风险信号
        for risk_indicator in self.financial_keywords["risk_indicators"]:
            if risk_indicator in chunk_lower:
                features["risk_signals"] += 1
        
        # 计算金融术语
        for financial_term in self.financial_keywords["financial_metrics"]:
            if financial_term in chunk_lower:
                features["financial_terms"] += 1
        
        # 计算监管提及
        for regulation in self.financial_keywords["regulations"]:
            if regulation.lower() in chunk_lower:
                features["regulatory_mentions"] += 1
        
        # 情感指标
        negative_indicators = ["risk", "loss", "decline", "decrease", "negative", "adverse", "concern", "issue", "problem", "threat"]
        positive_indicators = ["improve", "increase", "growth", "positive", "strong", "effective", "successful", "opportunity"]
        
        for indicator in negative_indicators:
            if indicator in chunk_lower:
                features["sentiment_indicators"].append(("negative", indicator))
        
        for indicator in positive_indicators:
            if indicator in chunk_lower:
                features["sentiment_indicators"].append(("positive", indicator))
        
        return features

    def _classify_chunk_type(self, chunk: str, features: Dict[str, Any]) -> str:
        """分类chunk类型"""
        chunk_lower = chunk.lower()
        
        # 风险披露
        if any(word in chunk_lower for word in ["risk factor", "item 1a", "risk management", "risk assessment"]):
            return "risk_disclosure"
        
        # 财务数据
        elif any(word in chunk_lower for word in ["financial statement", "balance sheet", "income statement", "cash flow"]):
            return "financial_data"
        
        # 合规相关
        elif any(word in chunk_lower for word in ["internal control", "sox", "compliance", "audit"]):
            return "compliance"
        
        # 管理层分析
        elif any(word in chunk_lower for word in ["management discussion", "md&a", "outlook", "forward-looking"]):
            return "management_analysis"
        
        # 监管相关
        elif features["regulatory_mentions"] > 0:
            return "regulatory"
        
        # 风险评估
        elif features["risk_signals"] > 2:
            return "risk_assessment"
        
        # 财务指标
        elif features["financial_terms"] > 1:
            return "financial_metrics"
        
        else:
            return "general"

    def _calculate_importance_score(self, chunk: str, features: Dict[str, Any]) -> float:
        """计算chunk重要性分数"""
        score = 0.0
        
        # 基于长度的分数
        word_count = len(chunk.split())
        if 50 <= word_count <= 200:
            score += 0.2
        elif word_count > 200:
            score += 0.1
        
        # 基于风险信号的分数
        score += min(features["risk_signals"] / 10, 0.3)
        
        # 基于金融术语的分数
        score += min(features["financial_terms"] / 10, 0.2)
        
        # 基于监管提及的分数
        score += min(features["regulatory_mentions"] / 5, 0.2)
        
        # 基于实体数量的分数
        score += min(len(features["entities"]) / 10, 0.1)
        
        return min(score, 1.0)

    async def _enhance_chunks_with_entities(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """使用实体信息增强chunks"""
        enhanced = []
        
        for chunk_data in chunks:
            chunk = chunk_data["content"]
            metadata = chunk_data["metadata"]
            
            # 生成摘要
            chunk_summary = await self._generate_chunk_summary(chunk)
            
            # 提取关键词
            keywords = self._extract_chunk_keywords(chunk)
            
            enhanced_chunk = {
                "content": chunk,
                "metadata": {
                    **metadata,
                    "summary": chunk_summary,
                    "keywords": keywords,
                    "enhanced_at": datetime.now().isoformat()
                }
            }
            enhanced.append(enhanced_chunk)
        
        return enhanced

    async def _generate_chunk_summary(self, chunk: str) -> str:
        """生成chunk摘要"""
        if len(chunk) < 200:
            return chunk[:100] + "..."
        
        try:
            summary_prompt = ChatPromptTemplate.from_template("""
            请为以下金融文档片段生成一个简洁的摘要（不超过50字）：
            文档片段：{chunk}
            摘要：
            """)
            
            chain = summary_prompt | self.llm | StrOutputParser()
            summary = await asyncio.to_thread(chain.invoke, {"chunk": chunk[:1000]})
            return summary.strip()
            
        except Exception as e:
            logging.warning(f"摘要生成失败: {e}")
            return chunk[:100] + "..."

    def _extract_chunk_keywords(self, chunk: str) -> List[str]:
        """提取chunk关键词"""
        keywords = []
        chunk_lower = chunk.lower()
        
        # 从预定义词典提取关键词
        for category, word_list in self.financial_keywords.items():
            for word in word_list:
                if word in chunk_lower:
                    keywords.append(word)
        
        # 使用NLP提取实体关键词
        if self.nlp:
            try:
                doc = self.nlp(chunk)
                for ent in doc.ents:
                    if ent.label_ in ["ORG", "MONEY", "PERCENT", "LAW", "PERSON"]:
                        keywords.append(ent.text.lower())
            except Exception:
                pass
        
        # 去重并限制数量
        return list(set(keywords))[:10]

    # ===== 查询相关方法 =====

    async def intelligent_qa(
        self, 
        query: str, 
        vectorstore: FAISS, 
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """智能问答系统"""
        start_time = time.time()
        
        try:
            # 预处理查询
            processed_query = await self._preprocess_query(query, conversation_history)
            
            # 检索相关文档
            relevant_docs = await self._advanced_retrieve(processed_query, vectorstore)
            
            # 多跳推理（如果需要）
            if self._requires_multi_hop_reasoning(processed_query):
                relevant_docs = await self._multi_hop_retrieval(processed_query, vectorstore, relevant_docs)
            
            # 生成动态提示词
            qa_prompt = await self._generate_dynamic_prompt(processed_query, relevant_docs)
            
            # 生成答案
            answer = await self._generate_answer(qa_prompt, processed_query, relevant_docs)
            
            # 后处理答案
            final_answer = await self._post_process_answer(answer, processed_query, relevant_docs)
            
            # 计算置信度
            confidence_score = self._calculate_confidence(processed_query, relevant_docs, final_answer)
            
            # 生成引用
            citations = self._generate_citations(relevant_docs)
            
            # 生成解释
            explanation = await self._generate_explanation(processed_query, final_answer, relevant_docs)
            
            processing_time = time.time() - start_time
            
            return {
                "query": query,
                "answer": final_answer,
                "confidence_score": confidence_score,
                "citations": citations,
                "explanation": explanation,
                "relevant_documents": [
                    {
                        "content": doc.page_content[:200] + "...",
                        "metadata": doc.metadata,
                        "relevance_score": doc.metadata.get("rerank_score", 0)
                    }
                    for doc in relevant_docs
                ],
                "processing_time": processing_time,
                "retrieval_strategy": "advanced_hybrid",
                "documents_retrieved": len(relevant_docs)
            }
            
        except Exception as e:
            logging.error(f"智能问答失败: {e}")
            return {
                "query": query,
                "answer": f"抱歉，处理查询时出现错误: {str(e)}",
                "confidence_score": 0.0,
                "citations": [],
                "explanation": "系统错误",
                "relevant_documents": [],
                "processing_time": time.time() - start_time,
                "retrieval_strategy": "error",
                "documents_retrieved": 0
            }

    async def _preprocess_query(self, query: str, conversation_history: List[Dict[str, str]] = None) -> str:
        """查询预处理"""
        processed = query.strip()
        
        # 添加对话上下文
        if conversation_history:
            context = self._extract_conversation_context(conversation_history)
            if context:
                processed = f"{context} {processed}"
        
        # 扩展金融术语
        expanded = await self._expand_financial_terms(processed)
        
        return expanded

    def _extract_conversation_context(self, history: List[Dict[str, str]]) -> str:
        """提取对话上下文"""
        if not history:
            return ""
        
        recent_context = []
        for item in history[-2:]:  # 只取最近2轮对话
            if item.get("role") == "user":
                recent_context.append(f"之前问题：{item.get('content', '')}")
        
        return " ".join(recent_context)

    async def _expand_financial_terms(self, query: str) -> str:
        """扩展金融术语"""
        query_lower = query.lower()
        expansions = []
        
        # 风险相关扩展
        if "risk" in query_lower:
            risk_context = [
                rt for rt in self.financial_keywords["risk_types"] 
                if any(word in query_lower for word in rt.split())
            ]
            if risk_context:
                expansions.extend(risk_context[:3])
        
        # 监管相关扩展
        for regulation in self.financial_keywords["regulations"]:
            if regulation.lower() in query_lower:
                expansions.append(f"{regulation} compliance")
        
        if expansions:
            return f"{query} ({' OR '.join(expansions)})"
        
        return query

    async def _advanced_retrieve(self, query: str, vectorstore: FAISS) -> List[Document]:
        """高级检索策略"""
        logging.info(f"🔍 开始高级检索：{query[:50]}...")
        
        try:
            # 基础向量相似性搜索
            documents = await asyncio.to_thread(
                vectorstore.similarity_search, 
                query, 
                k=self.config["retrieval_k"]
            )
            
            # 关键词过滤
            filtered_docs = self._keyword_filter(query, documents)
            
            # 智能重排序
            if self.config["use_reranking"] and len(filtered_docs) > self.config["rerank_top_k"]:
                reranked_docs = await self._intelligent_reranking(query, filtered_docs)
            else:
                reranked_docs = filtered_docs
            
            # 上下文压缩
            if self.config["use_compression"] and len(reranked_docs) > 3:
                compressed_docs = await self._compress_context(query, reranked_docs)
            else:
                compressed_docs = reranked_docs
            
            logging.info(f"✅ 检索完成，返回 {len(compressed_docs)} 个相关文档")
            return compressed_docs
            
        except Exception as e:
            logging.error(f"检索失败: {e}")
            return []

    def _keyword_filter(self, query: str, docs: List[Document]) -> List[Document]:
        """基于关键词过滤文档"""
        query_terms = set(query.lower().split())
        filtered_docs = []
        
        for doc in docs:
            content_lower = doc.page_content.lower()
            
            # 计算关键词匹配分数
            keyword_score = sum(1 for term in query_terms if term in content_lower) / len(query_terms)
            
            # 计算金融术语匹配分数
            financial_score = 0
            for category, terms in self.financial_keywords.items():
                for term in terms:
                    if term in content_lower and any(qt in term for qt in query_terms):
                        financial_score += 1
            
            # 综合分数
            total_score = keyword_score * 0.7 + min(financial_score / 10, 1.0) * 0.3
            
            if total_score > self.config["similarity_threshold"] * 0.5:
                doc.metadata["keyword_score"] = keyword_score
                doc.metadata["financial_score"] = financial_score
                doc.metadata["total_score"] = total_score
                filtered_docs.append(doc)
        
        # 按分数排序
        return sorted(filtered_docs, key=lambda x: x.metadata.get("total_score", 0), reverse=True)

    async def _intelligent_reranking(self, query: str, documents: List[Document]) -> List[Document]:
        """智能重排序"""
        reranked = []
        
        for doc in documents:
            rerank_score = await self._calculate_rerank_score(query, doc)
            doc.metadata["rerank_score"] = rerank_score
            reranked.append(doc)
        
        # 按重排序分数排序
        reranked.sort(key=lambda x: x.metadata.get("rerank_score", 0), reverse=True)
        
        return reranked[:self.config["rerank_top_k"]]

    async def _calculate_rerank_score(self, query: str, document: Document) -> float:
        """计算重排序分数"""
        score = 0.0
        
        # 语义相似性分数（如果有sentence transformer）
        if self.sentence_model:
            try:
                query_embedding = self.sentence_model.encode([query])
                doc_embedding = self.sentence_model.encode([document.page_content[:500]])
                semantic_similarity = util.cos_sim(query_embedding, doc_embedding)[0][0].item()
                score += semantic_similarity * 0.4
            except Exception:
                score += 0.2  # 默认分数
        else:
            score += 0.2
        
        # 关键词匹配分数
        keyword_score = document.metadata.get("keyword_score", 0)
        score += keyword_score * 0.3
        
        # 重要性分数
        importance_score = document.metadata.get("importance_score", 0.5)
        score += importance_score * 0.2
        
        # 文档类型权重
        chunk_type = document.metadata.get("chunk_type", "general")
        type_weights = {
            "risk_disclosure": 1.0,
            "compliance": 0.9,
            "financial_data": 0.8,
            "management_analysis": 0.7,
            "regulatory": 0.8,
            "risk_assessment": 0.9,
            "general": 0.5
        }
        score += type_weights.get(chunk_type, 0.5) * 0.1
        
        return min(score, 1.0)

    async def _compress_context(self, query: str, documents: List[Document]) -> List[Document]:
        """上下文压缩"""
        if len(documents) <= 3:
            return documents
        
        compression_prompt = ChatPromptTemplate.from_template("""
        作为金融风险分析专家，请从以下文档片段中提取与查询最相关的关键信息。
        保持原文的重要细节，但去除冗余内容。
        
        查询：{query}
        文档内容：{context}
        
        请提取最相关的信息（保持原文表述）：
        """)
        
        compressed_docs = []
        for doc in documents:
            try:
                chain = compression_prompt | self.llm | StrOutputParser()
                compressed_content = await asyncio.to_thread(
                    chain.invoke, 
                    {"query": query, "context": doc.page_content[:1500]}
                )
                
                compressed_doc = Document(
                    page_content=compressed_content.strip(),
                    metadata={
                        **doc.metadata,
                        "compressed": True,
                        "original_length": len(doc.page_content),
                        "compressed_length": len(compressed_content)
                    }
                )
                compressed_docs.append(compressed_doc)
                
            except Exception as e:
                logging.warning(f"压缩失败，保留原文档: {e}")
                compressed_docs.append(doc)
        
        return compressed_docs

    def _requires_multi_hop_reasoning(self, query: str) -> bool:
        """判断是否需要多跳推理"""
        multi_hop_indicators = [
            "compare", "relationship", "impact", "cause", "effect", 
            "correlation", "trend", "change", "difference", "connection"
        ]
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in multi_hop_indicators)

    async def _multi_hop_retrieval(self, query: str, vectorstore: FAISS, initial_docs: List[Document]) -> List[Document]:
        """多跳检索"""
        # 从初始文档中提取关键概念
        key_concepts = await self._extract_key_concepts_from_docs(initial_docs)
        
        additional_docs = []
        for concept in key_concepts[:3]:  # 只取前3个概念
            concept_query = f"{concept} {query}"
            try:
                concept_docs = await asyncio.to_thread(vectorstore.similarity_search, concept_query, k=3)
                additional_docs.extend(concept_docs)
            except Exception as e:
                logging.warning(f"概念查询失败 {concept}: {e}")
        
        # 合并并去重
        all_docs = initial_docs + additional_docs
        return self._deduplicate_documents(all_docs)[:self.config["rerank_top_k"]]

    async def _extract_key_concepts_from_docs(self, docs: List[Document]) -> List[str]:
        """从文档中提取关键概念"""
        key_concepts = []
        
        for doc in docs[:3]:  # 只分析前3个文档
            content_lower = doc.page_content.lower()
            
            # 提取金融关键词
            for category, terms in self.financial_keywords.items():
                for term in terms:
                    if term in content_lower:
                        key_concepts.append(term)
        
        # 统计并返回最常见的概念
        concept_counts = Counter(key_concepts)
        return [concept for concept, count in concept_counts.most_common(5)]

    def _deduplicate_documents(self, docs: List[Document]) -> List[Document]:
        """文档去重"""
        seen_content = set()
        unique_docs = []
        
        for doc in docs:
            # 使用前100个字符作为内容签名
            content_signature = doc.page_content[:100]
            if content_signature not in seen_content:
                seen_content.add(content_signature)
                unique_docs.append(doc)
        
        return unique_docs

    async def _generate_dynamic_prompt(self, query: str, documents: List[Document]) -> ChatPromptTemplate:
        """动态生成提示词"""
        # 分类查询类型
        query_type = self._classify_query_type(query)
        
        # 分析文档类型
        doc_types = [doc.metadata.get("chunk_type", "general") for doc in documents]
        dominant_doc_type = Counter(doc_types).most_common(1)[0][0] if doc_types else "general"
        
        # 选择合适的提示词模板
        prompt_template = self._select_prompt_template(query_type, dominant_doc_type)
        
        return ChatPromptTemplate.from_template(prompt_template)

    def _classify_query_type(self, query: str) -> str:
        """分类查询类型"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["risk", "exposure", "threat", "vulnerability"]):
            return "risk_analysis"
        elif any(word in query_lower for word in ["compliance", "regulation", "sox", "sec"]):
            return "compliance"
        elif any(word in query_lower for word in ["financial", "revenue", "profit", "loss", "metric"]):
            return "financial_analysis"
        elif any(word in query_lower for word in ["compare", "difference", "vs", "versus"]):
            return "comparison"
        elif any(word in query_lower for word in ["trend", "change", "over time", "historical"]):
            return "trend_analysis"
        else:
            return "general"

    def _select_prompt_template(self, query_type: str, doc_type: str) -> str:
        """选择适合的提示词模板"""
        base_template = """
您是一位资深的金融风险分析专家，具有深厚的10-K文档分析经验。
请基于以下文档内容回答用户的问题：

相关文档：
{context}

用户问题：
{question}

回答要求：
"""
        
        if query_type == "risk_analysis":
            base_template += """- 重点分析风险类型、严重程度和潜在影响
- 引用具体的风险因素和数据
- 评估风险的可控性和缓解措施
- 如果涉及监管风险，请明确相关法规条款
"""
        elif query_type == "compliance":
            base_template += """- 明确指出相关的监管要求和合规状态
- 引用具体的法规条款（如SOX 404、SEC Item 105等）
- 分析合规缺陷的严重性和整改要求
- 评估对业务运营的影响
"""
        elif query_type == "financial_analysis":
            base_template += """- 提供具体的财务数据和指标
- 分析财务趋势和变化原因
- 评估对公司财务健康状况的影响
- 如有同比数据，请进行对比分析
"""
        elif query_type == "comparison":
            base_template += """- 进行详细的对比分析
- 突出显示关键差异和相似点
- 分析差异的原因和影响
- 提供数据支持的结论
"""
        else:
            base_template += """- 提供准确、具体的回答
- 引用相关的文档内容作为依据
- 如果信息不足，请明确说明
- 保持客观和专业的分析角度
"""
        
        base_template += """
注意事项：
- 如果文档中没有相关信息，请明确说明"文档中未找到相关信息"
- 引用时请保持原文的准确性
- 提供可信度评估（高/中/低）
- 如需要，可以提出进一步分析的建议

回答：
"""
        return base_template

    async def _generate_answer(self, prompt: ChatPromptTemplate, query: str, documents: List[Document]) -> str:
        """生成答案"""
        # 构建上下文
        context = "\n\n".join([
            f"文档 {i+1}:\n{doc.page_content}" 
            for i, doc in enumerate(documents[:5])  # 只使用前5个文档
        ])
        
        try:
            chain = prompt | self.llm | StrOutputParser()
            answer = await asyncio.to_thread(
                chain.invoke, 
                {"context": context, "question": query}
            )
            return answer.strip()
            
        except Exception as e:
            logging.error(f"答案生成失败: {e}")
            return "抱歉，在生成答案时遇到了问题。请尝试重新表述您的问题。"

    async def _post_process_answer(self, answer: str, query: str, documents: List[Document]) -> str:
        """答案后处理"""
        # 验证事实
        verified_answer = await self._verify_facts(answer, documents)
        
        # 格式化答案
        formatted_answer = self._format_answer(verified_answer)
        
        # 添加免责声明（如果需要）
        if self._requires_disclaimer(query):
            formatted_answer += "\n\n⚠️ 免责声明：本分析基于提供的文档内容，仅供参考。具体决策请咨询专业顾问。"
        
        return formatted_answer

    async def _verify_facts(self, answer: str, documents: List[Document]) -> str:
        """验证答案中的事实"""
        # 提取答案中的数字
        numbers = re.findall(r'\d+(?:\.\d+)?%?', answer)
        
        # 检查这些数字是否在原文档中
        all_doc_content = " ".join([doc.page_content for doc in documents])
        verified_numbers = [num for num in numbers if num in all_doc_content]
        
        # 计算验证比例
        verification_ratio = len(verified_numbers) / len(numbers) if numbers else 1.0
        
        if verification_ratio < 0.5:
            answer = f"⚠️ 部分信息可能需要进一步验证\n\n{answer}"
        
        return answer

    def _format_answer(self, answer: str) -> str:
        """格式化答案"""
        formatted = answer
        
        # 为长答案添加段落分隔
        if len(formatted) > 500:
            formatted = re.sub(r'。([^。]{100,})', r'。\n\n\1', formatted)
        
        return formatted

    def _requires_disclaimer(self, query: str) -> bool:
        """判断是否需要添加免责声明"""
        disclaimer_triggers = [
            "investment", "invest", "buy", "sell", "recommendation", 
            "advice", "should", "suggest", "recommend"
        ]
        query_lower = query.lower()
        return any(trigger in query_lower for trigger in disclaimer_triggers)

    def _calculate_confidence(self, query: str, documents: List[Document], answer: str) -> float:
        """计算答案置信度"""
        confidence = 0.0
        
        # 文档质量分数
        doc_quality = np.mean([doc.metadata.get("rerank_score", 0.5) for doc in documents])
        confidence += doc_quality * 0.4
        
        # 答案完整性分数
        answer_completeness = min(len(answer) / 500, 1.0)
        confidence += answer_completeness * 0.2
        
        # 关键词匹配分数
        query_terms = set(query.lower().split())
        answer_terms = set(answer.lower().split())
        keyword_match = len(query_terms.intersection(answer_terms)) / len(query_terms)
        confidence += keyword_match * 0.2
        
        # 文档数量分数
        doc_count_score = min(len(documents) / 5, 1.0)
        confidence += doc_count_score * 0.1
        
        # 具体数据分数
        has_specific_data = bool(re.search(r'\d+(?:\.\d+)?[%$]?', answer))
        if has_specific_data:
            confidence += 0.1
        
        return min(confidence, 1.0)

    def _generate_citations(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """生成引用信息"""
        citations = []
        
        for i, doc in enumerate(documents):
            citation = {
                "id": i + 1,
                "content_preview": doc.page_content[:150] + "...",
                "relevance_score": doc.metadata.get("rerank_score", 0),
                "document_type": doc.metadata.get("chunk_type", "unknown"),
                "metadata": {
                    k: v for k, v in doc.metadata.items() 
                    if k in ["document_index", "chunk_index", "importance_score"]
                }
            }
            citations.append(citation)
        
        return citations

    async def _generate_explanation(self, query: str, answer: str, documents: List[Document]) -> str:
        """生成回答解释"""
        explanation_prompt = ChatPromptTemplate.from_template("""
请为以下问答对生成一个简短的解释，说明答案的依据和推理过程：

问题：{query}
答案：{answer}
使用的文档数量：{doc_count}

解释（不超过100字）：
""")
        
        try:
            chain = explanation_prompt | self.llm | StrOutputParser()
            explanation = await asyncio.to_thread(
                chain.invoke, 
                {
                    "query": query, 
                    "answer": answer[:500], 
                    "doc_count": len(documents)
                }
            )
            return explanation.strip()
            
        except Exception as e:
            logging.warning(f"解释生成失败: {e}")
            return f"基于 {len(documents)} 个相关文档片段生成的答案"

    # ===== 简单RAG链方法（兼容原有EnhancedRAGChain） =====

    def build_smart_rag_chain(self, vectorstore, query_type: str = "general") -> RetrievalQA:
        """构建智能RAG链（兼容原有接口）"""
        try:
            # 生成提示词模板
            prompt_template = self._get_prompt_by_type(query_type)
            
            # 创建检索器
            retriever = vectorstore.as_retriever(search_kwargs={"k": self.config["retrieval_k"]})
            
            # 构建RAG链
            rag_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                retriever=retriever,
                chain_type="stuff",
                chain_type_kwargs={"prompt": prompt_template},
                return_source_documents=True
            )
            
            return rag_chain
            
        except Exception as e:
            logging.error(f"构建RAG链失败: {e}")
            raise

    def _get_prompt_by_type(self, query_type: str) -> ChatPromptTemplate:
        """根据查询类型获取提示词（兼容原有接口）"""
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


# 测试函数
async def test_unified_rag():
    """测试统一RAG系统"""
    rag_service = UnifiedRAGService()
    
    test_documents = [
        "公司面临的主要风险包括市场风险、信用风险和操作风险。市场风险主要来自利率变化和汇率波动，预计可能导致年度收益下降5-10%。",
        "根据SOX 404条款要求，公司建立了内部控制制度。但在2023年度审计中发现了一项重大缺陷，涉及收入确认流程。",
        "公司的流动性比率为1.5，债务权益比为0.8。现金流量表显示经营活动现金流为正，但投资活动现金流为负。"
    ]
    
    test_metadata = [
        {"document_type": "10-K", "section": "Risk Factors"},
        {"document_type": "10-K", "section": "Internal Controls"},
        {"document_type": "10-K", "section": "Financial Statements"}
    ]
    
    print("🔄 构建向量数据库...")
    vectorstore = await rag_service.build_enhanced_vectorstore(
        test_documents, 
        test_metadata, 
        save_path="test_vectorstore"
    )
    
    test_queries = [
        "公司面临哪些主要风险？",
        "SOX合规状况如何？",
        "公司的财务状况是否健康？",
        "市场风险对公司的影响有多大？"
    ]
    
    for query in test_queries:
        print(f"\n🔍 测试查询：{query}")
        result = await rag_service.intelligent_qa(query, vectorstore)
        print(f"答案：{result['answer']}")
        print(f"置信度：{result['confidence_score']:.2f}")
        print(f"检索文档数：{result['documents_retrieved']}")
        print(f"处理时间：{result['processing_time']:.2f}秒")


if __name__ == "__main__":
    asyncio.run(test_unified_rag())
