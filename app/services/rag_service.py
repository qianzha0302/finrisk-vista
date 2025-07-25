# services/advanced_rag_service.py
"""
高级RAG服务 - 针对金融风险分析优化的检索增强生成系统
Features:
- 混合检索（向量+关键词+语义）
- 智能重排序
- 上下文压缩
- 多跳推理
- 实体识别和关联
- 动态提示词生成
"""

import asyncio
import json
import time
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime

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
import re
from collections import Counter, defaultdict
from dotenv import load_dotenv
import os
from ..utils.rag_config import RAGConfig

# 加载 .env 文件
load_dotenv()

class AdvancedRAGService:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = {**RAGConfig.get_config(), **(config or {})}  # 合并默认和自定义配置
        self.llm = ChatOpenAI(
            model=RAGConfig.LLM_MODEL,
            api_key=os.getenv("OPENAI_API_KEY", ""),
            temperature=self.config["llm_temperature"],
            max_tokens=self.config["max_tokens"]
        )
        self.embedding_model = OpenAIEmbeddings(
            api_key=os.getenv("OPENAI_API_KEY", "")
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config["chunk_size"],
            chunk_overlap=self.config["chunk_overlap"],
            separators=["\n\n", "\n", ". ", "。", "；", ";", ":", "：", " "]
        )
        self.nlp = spacy.load("en_core_web_sm") if spacy else None
        self.sentence_model = SentenceTransformer(RAGConfig.SENTENCE_MODEL) if sentence_transformers else None
        self.financial_keywords = self._load_financial_keywords()
        self.risk_entities = self._load_risk_entities()
        self.vectorstore_cache = {}
        self.query_cache = {}

    def _load_financial_keywords(self) -> Dict[str, List[str]]:
        """加载金融关键词词典"""
        return {
            "risk_types": [...],  # 保持原列表，略去以节省空间
            "financial_metrics": [...],
            "regulations": [...],
            "risk_indicators": [...],
            "financial_statements": [...]
        }

    def _load_risk_entities(self) -> Dict[str, Any]:
        """加载风险实体模式"""
        return {
            "monetary_patterns": [...],  # 保持原列表
            "percentage_patterns": [...],
            "date_patterns": [...],
            "risk_severity_patterns": [...]
        }

    async def build_enhanced_vectorstore(self, documents: List[str], document_metadata: List[Dict[str, Any]], save_path: Optional[str] = None) -> FAISS:
        """构建增强的向量数据库"""
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
            await asyncio.to_thread(vectorstore.save_local, save_path)
            metadata_path = f"{save_path}_metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump({"chunks": enhanced_chunks, "build_time": datetime.now().isoformat(), "config": self.config}, f, ensure_ascii=False, indent=2)
        print(f"✅ 向量数据库构建完成，包含 {len(enhanced_chunks)} 个增强块")
        return vectorstore

    async def _preprocess_documents(self, documents: List[str], metadata: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """智能文档预处理"""
        processed = []
        for i, (doc, meta) in enumerate(zip(documents, metadata)):
            cleaned_text = self._clean_text(doc)
            sections = self._identify_document_sections(cleaned_text)
            key_info = self._extract_key_information(cleaned_text)
            processed.append({"content": cleaned_text, "metadata": {**meta, "sections": sections, "key_info": key_info, "document_index": i, "processed_at": datetime.now().isoformat()}})
        return processed

    def _clean_text(self, text: str) -> str:
        """文本清理"""
        text = re.sub(r'\s+', ' ', text)
        text = text.replace('"', '"').replace('"', '"').replace(''', "'").replace(''', "'")
        text = re.sub(r'Page \d+ of \d+', '', text)
        text = re.sub(r'\d+\s*$', '', text, flags=re.MULTILINE)
        text = text.replace('l0', '10').replace('O0', '00')
        return text.strip()

    def _identify_document_sections(self, text: str) -> List[str]:
        """识别文档章节"""
        sections = []
        section_patterns = [r'Item\s+\d+[A-Z]?\.\s+([^\.]+)', r'PART\s+[IVX]+\s*[-–]?\s*([^\.]+)', r'(?:^|\n)\s*(\d+\.\s+[^\.]+)', r'(?:^|\n)\s*([A-Z][^\.]{5,50})\s*(?:\n|$)']
        for pattern in section_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            sections.extend([match.strip() for match in matches if len(match.strip()) > 3])
        return list(set(sections))[:10]

    def _extract_key_information(self, text: str) -> Dict[str, Any]:
        """提取关键信息"""
        key_info = {"monetary_amounts": [], "percentages": [], "dates": [], "risk_mentions": [], "regulatory_references": []}
        for pattern in self.risk_entities["monetary_patterns"]:
            matches = re.findall(pattern, text, re.IGNORECASE)
            key_info["monetary_amounts"].extend(matches[:5])
        for pattern in self.risk_entities["percentage_patterns"]:
            matches = re.findall(pattern, text)
            key_info["percentages"].extend(matches[:10])
        for pattern in self.risk_entities["date_patterns"]:
            matches = re.findall(pattern, text)
            key_info["dates"].extend(matches[:5])
        text_lower = text.lower()
        for risk_type in self.financial_keywords["risk_types"]:
            if risk_type in text_lower:
                key_info["risk_mentions"].append(risk_type)
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
            base_chunks = self.text_splitter.split_text(content)
            semantic_chunks = await self._semantic_chunking(base_chunks, metadata)
            all_chunks.extend(semantic_chunks)
        return all_chunks

    async def _semantic_chunking(self, chunks: List[str], base_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """基于语义的智能分块"""
        enhanced_chunks = []
        for i, chunk in enumerate(chunks):
            semantic_features = await self._analyze_chunk_semantics(chunk)
            chunk_type = self._classify_chunk_type(chunk, semantic_features)
            importance_score = self._calculate_importance_score(chunk, semantic_features)
            enhanced_chunks.append({
                "content": chunk,
                "metadata": {
                    **base_metadata,
                    "chunk_index": i,
                    "chunk_type": chunk_type,
                    "importance_score": importance_score,
                    "semantic_features": semantic_features,
                    "word_count": len(chunk.split()),
                    "has_numbers": bool(re.search(r'\d', chunk)),
                    "has_risk_keywords": any(keyword in chunk.lower() for keyword_list in self.financial_keywords.values() for keyword in keyword_list)
                }
            })
        return enhanced_chunks

    async def _analyze_chunk_semantics(self, chunk: str) -> Dict[str, Any]:
        """分析chunk的语义特征"""
        features = {"entities": [], "risk_signals": 0, "financial_terms": 0, "regulatory_mentions": 0, "sentiment_indicators": []}
        if self.nlp:
            doc = self.nlp(chunk)
            features["entities"] = [{"text": ent.text, "label": ent.label_} for ent in doc.ents if ent.label_ in ["ORG", "MONEY", "PERCENT", "DATE", "LAW"]]
        chunk_lower = chunk.lower()
        for risk_indicator in self.financial_keywords["risk_indicators"]:
            if risk_indicator in chunk_lower:
                features["risk_signals"] += 1
        for financial_term in self.financial_keywords["financial_metrics"]:
            if financial_term in chunk_lower:
                features["financial_terms"] += 1
        for regulation in self.financial_keywords["regulations"]:
            if regulation.lower() in chunk_lower:
                features["regulatory_mentions"] += 1
        negative_indicators = ["risk", "loss", "decline", "decrease", "negative", "adverse", "concern", "issue", "problem"]
        positive_indicators = ["improve", "increase", "growth", "positive", "strong", "effective", "successful"]
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
        if any(word in chunk_lower for word in ["risk factor", "item 1a", "risk management"]):
            return "risk_disclosure"
        elif any(word in chunk_lower for word in ["financial statement", "balance sheet", "income statement"]):
            return "financial_data"
        elif any(word in chunk_lower for word in ["internal control", "sox", "compliance"]):
            return "compliance"
        elif any(word in chunk_lower for word in ["management discussion", "md&a", "outlook"]):
            return "management_analysis"
        elif features["regulatory_mentions"] > 0:
            return "regulatory"
        elif features["risk_signals"] > 2:
            return "risk_assessment"
        elif features["financial_terms"] > 1:
            return "financial_metrics"
        else:
            return "general"

    def _calculate_importance_score(self, chunk: str, features: Dict[str, Any]) -> float:
        """计算chunk重要性分数"""
        score = 0.0
        score += min(len(chunk.split()) / 100, 1.0) * 0.2
        score += min(features["risk_signals"] / 10, 1.0) * 0.3
        score += min(features["financial_terms"] / 10, 1.0) * 0.2
        score += min(features["regulatory_mentions"] / 5, 1.0) * 0.2
        score += min(len(features["entities"]) / 10, 1.0) * 0.1
        return min(score, 1.0)

    async def _enhance_chunks_with_entities(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """使用实体信息增强chunks"""
        enhanced = []
        for chunk_data in chunks:
            chunk = chunk_data["content"]
            metadata = chunk_data["metadata"]
            annotated_chunk = await self._annotate_entities(chunk)
            chunk_summary = await self._generate_chunk_summary(chunk)
            keywords = self._extract_chunk_keywords(chunk)
            enhanced.append({
                "content": annotated_chunk,
                "metadata": {**metadata, "summary": chunk_summary, "keywords": keywords, "enhanced_at": datetime.now().isoformat()}
            })
        return enhanced

    async def _annotate_entities(self, text: str) -> str:
        """标注实体"""
        annotated = text
        for pattern in self.risk_entities["monetary_patterns"]:
            annotated = re.sub(pattern, r'<MONEY>\g<0></MONEY>', annotated, flags=re.IGNORECASE)
        for pattern in self.risk_entities["percentage_patterns"]:
            annotated = re.sub(pattern, r'<PERCENT>\g<0></PERCENT>', annotated)
        return annotated

    async def _generate_chunk_summary(self, chunk: str) -> str:
        """生成chunk摘要"""
        if len(chunk) < 200:
            return chunk[:100] + "..."
        summary_prompt = ChatPromptTemplate.from_template("""
        请为以下金融文档片段生成一个简洁的摘要（不超过50字）：
        文档片段：{chunk}
        摘要：
        """)
        try:
            chain = summary_prompt | self.llm | StrOutputParser()
            summary = await asyncio.to_thread(chain.invoke, {"chunk": chunk[:1000]})
            return summary.strip()
        except Exception as e:
            print(f"摘要生成失败: {e}")
            return chunk[:100] + "..."

    def _extract_chunk_keywords(self, chunk: str) -> List[str]:
        """提取chunk关键词"""
        keywords = []
        chunk_lower = chunk.lower()
        for category, word_list in self.financial_keywords.items():
            for word in word_list:
                if word in chunk_lower:
                    keywords.append(word)
        if self.nlp:
            doc = self.nlp(chunk)
            for ent in doc.ents:
                if ent.label_ in ["ORG", "MONEY", "PERCENT", "LAW"]:
                    keywords.append(ent.text.lower())
        return list(set(keywords))[:10]

    async def advanced_retrieve(self, query: str, vectorstore: FAISS, retrieval_strategy: str = "hybrid") -> List[Document]:
        """高级检索策略"""
        print(f"🔍 开始高级检索：{query}")
        enhanced_queries = await self._enhance_query(query)
        if retrieval_strategy == "hybrid":
            documents = await self._hybrid_retrieval(enhanced_queries, vectorstore)
        elif retrieval_strategy == "semantic":
            documents = await self._semantic_retrieval(enhanced_queries, vectorstore)
        elif retrieval_strategy == "keyword":
            documents = await self._keyword_retrieval(enhanced_queries, vectorstore)
        else:
            documents = await self._ensemble_retrieval(enhanced_queries, vectorstore)
        if self.config["use_reranking"]:
            documents = await self._intelligent_reranking(query, documents)
        if self.config["use_compression"]:
            documents = await self._compress_context(query, documents)
        print(f"✅ 检索完成，返回 {len(documents)} 个相关文档")
        return documents

    async def _enhance_query(self, query: str) -> List[str]:
        """查询增强和扩展"""
        enhanced_queries = [query]
        synonyms = await self._get_financial_synonyms(query)
        if synonyms:
            enhanced_queries.extend(synonyms[:3])
        if self.config["enable_multi_query"]:
            multi_queries = await self._generate_multi_perspective_queries(query)
            enhanced_queries.extend(multi_queries[:2])
        entities = self._extract_query_entities(query)
        if entities:
            entity_expanded_query = await self._expand_with_entities(query, entities)
            enhanced_queries.append(entity_expanded_query)
        return enhanced_queries

    async def _get_financial_synonyms(self, query: str) -> List[str]:
        """获取金融领域同义词"""
        financial_synonyms = {"risk": ["exposure", "hazard", "vulnerability", "threat"], "loss": ["deficit", "shortfall", "decline", "reduction"], "profit": ["earnings", "income", "revenue", "gains"], "compliance": ["adherence", "conformity", "regulation"], "audit": ["review", "examination", "assessment", "evaluation"]}
        synonyms = []
        query_lower = query.lower()
        for word, syn_list in financial_synonyms.items():
            if word in query_lower:
                for synonym in syn_list:
                    synonym_query = query_lower.replace(word, synonym)
                    synonyms.append(synonym_query)
        return synonyms

    async def _generate_multi_perspective_queries(self, query: str) -> List[str]:
        """生成多角度查询"""
        multi_query_prompt = ChatPromptTemplate.from_template("""
        作为金融风险分析专家，请为以下查询生成2个不同角度的相关问题，用于检索10-K文档：
        原始查询：{query}
        请生成：
        1. 一个更具体的查询
        2. 一个更广泛的相关查询
        格式：每行一个查询，不要编号
        """)
        try:
            chain = multi_query_prompt | self.llm | StrOutputParser()
            result = await asyncio.to_thread(chain.invoke, {"query": query})
            queries = [line.strip() for line in result.split('\n') if line.strip()]
            return queries[:2]
        except Exception as e:
            print(f"多角度查询生成失败: {e}")
            return []

    def _extract_query_entities(self, query: str) -> List[Dict[str, str]]:
        """提取查询中的实体"""
        entities = []
        if self.nlp:
            doc = self.nlp(query)
            for ent in doc.ents:
                entities.append({"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char})
        return entities

    async def _expand_with_entities(self, query: str, entities: List[Dict[str, str]]) -> str:
        """基于实体扩展查询"""
        expanded_terms = []
        for entity in entities:
            if entity["label"] == "ORG":
                expanded_terms.append(f"{entity['text']} company")
            elif entity["label"] == "MONEY":
                expanded_terms.append(f"financial impact {entity['text']}")
        if expanded_terms:
            return f"{query} {' '.join(expanded_terms)}"
        return query

    async def _hybrid_retrieval(self, queries: List[str], vectorstore: FAISS) -> List[Document]:
        """混合检索：向量相似性 + 关键词匹配"""
        all_docs = []
        for query in queries:
            vector_docs = await asyncio.to_thread(vectorstore.similarity_search, query, k=self.config["retrieval_k"])
            keyword_filtered = self._keyword_filter(query, vector_docs)
            all_docs.extend(keyword_filtered)
        unique_docs = self._deduplicate_documents(all_docs)
        return unique_docs[:self.config["rerank_top_k"] * 2]

    def _keyword_filter(self, query: str, docs: List[Document]) -> List[Document]:
        """基于关键词过滤和评分文档"""
        query_terms = set(query.lower().split())
        filtered_docs = []
        for doc in docs:
            content_lower = doc.page_content.lower()
            keyword_score = sum(1 for term in query_terms if term in content_lower) / len(query_terms)
            financial_score = 0
            for category, terms in self.financial_keywords.items():
                for term in terms:
                    if term in content_lower and any(qt in term for qt in query_terms):
                        financial_score += 1
            total_score = keyword_score * 0.7 + min(financial_score / 10, 1.0) * 0.3
            if total_score > self.config["similarity_threshold"] * 0.5:
                doc.metadata["keyword_score"] = keyword_score
                doc.metadata["financial_score"] = financial_score
                doc.metadata["total_score"] = total_score
                filtered_docs.append(doc)
        return sorted(filtered_docs, key=lambda x: x.metadata.get("total_score", 0), reverse=True)

    def _deduplicate_documents(self, docs: List[Document]) -> List[Document]:
        """文档去重"""
        seen_content = set()
        unique_docs = []
        for doc in docs:
            content_signature = doc.page_content[:100]
            if content_signature not in seen_content:
                seen_content.add(content_signature)
                unique_docs.append(doc)
        return unique_docs

    async def _intelligent_reranking(self, query: str, documents: List[Document]) -> List[Document]:
        """智能重排序"""
        if len(documents) <= self.config["rerank_top_k"]:
            return documents
        reranked = []
        for doc in documents:
            rerank_score = await self._calculate_rerank_score(query, doc)
            doc.metadata["rerank_score"] = rerank_score
            reranked.append(doc)
        reranked.sort(key=lambda x: x.metadata.get("rerank_score", 0), reverse=True)
        return reranked[:self.config["rerank_top_k"]]

    async def _calculate_rerank_score(self, query: str, document: Document) -> float:
        """计算重排序分数"""
        score = 0.0
        if self.sentence_model:
            try:
                query_embedding = self.sentence_model.encode([query])
                doc_embedding = self.sentence_model.encode([document.page_content[:500]])
                semantic_similarity = util.cos_sim(query_embedding, doc_embedding)[0][0].item()
                score += semantic_similarity * 0.4
            except Exception:
                score += 0.2
        keyword_score = document.metadata.get("keyword_score", 0)
        score += keyword_score * 0.3
        importance_score = document.metadata.get("importance_score", 0.5)
        score += importance_score * 0.2
        chunk_type = document.metadata.get("chunk_type", "general")
        type_weights = {"risk_disclosure": 1.0, "compliance": 0.9, "financial_data": 0.8, "management_analysis": 0.7, "regulatory": 0.8, "risk_assessment": 0.9, "general": 0.5}
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
                compressed_content = await asyncio.to_thread(chain.invoke, {"query": query, "context": doc.page_content[:1500]})
                compressed_doc = Document(page_content=compressed_content.strip(), metadata={**doc.metadata, "compressed": True, "original_length": len(doc.page_content), "compressed_length": len(compressed_content)})
                compressed_docs.append(compressed_doc)
            except Exception as e:
                print(f"压缩失败，保留原文档: {e}")
                compressed_docs.append(doc)
        return compressed_docs

    async def intelligent_qa(self, query: str, vectorstore: FAISS, conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """智能问答系统"""
        start_time = time.time()
        processed_query = await self._preprocess_query(query, conversation_history)
        relevant_docs = await self.advanced_retrieve(processed_query, vectorstore)
        if self._requires_multi_hop_reasoning(processed_query):
            relevant_docs = await self._multi_hop_retrieval(processed_query, vectorstore, relevant_docs)
        qa_prompt = await self._generate_dynamic_prompt(processed_query, relevant_docs)
        answer = await self._generate_answer(qa_prompt, processed_query, relevant_docs)
        final_answer = await self._post_process_answer(answer, processed_query, relevant_docs)
        confidence_score = self._calculate_confidence(processed_query, relevant_docs, final_answer)
        citations = self._generate_citations(relevant_docs)
        explanation = await self._generate_explanation(processed_query, final_answer, relevant_docs)
        processing_time = time.time() - start_time
        return {
            "query": query,
            "answer": final_answer,
            "confidence_score": confidence_score,
            "citations": citations,
            "explanation": explanation,
            "relevant_documents": [{"content": doc.page_content[:200] + "...", "metadata": doc.metadata, "relevance_score": doc.metadata.get("rerank_score", 0)} for doc in relevant_docs],
            "processing_time": processing_time,
            "retrieval_strategy": "advanced_hybrid",
            "documents_retrieved": len(relevant_docs)
        }

    async def _preprocess_query(self, query: str, conversation_history: List[Dict[str, str]] = None) -> str:
        """查询预处理"""
        processed = query.strip()
        if conversation_history:
            context = self._extract_conversation_context(conversation_history)
            if context:
                processed = f"{context} {processed}"
        expanded = await self._expand_financial_terms(processed)
        return expanded

    def _extract_conversation_context(self, history: List[Dict[str, str]]) -> str:
        """提取对话上下文"""
        if not history or len(history) == 0:
            return ""
        recent_context = []
        for item in history[-2:]:
            if item.get("role") == "user":
                recent_context.append(f"之前问题：{item.get('content', '')}")
        return " ".join(recent_context)

    async def _expand_financial_terms(self, query: str) -> str:
        """扩展金融术语"""
        query_lower = query.lower()
        expansions = []
        if "risk" in query_lower:
            risk_context = [rt for rt in self.financial_keywords["risk_types"] if any(word in query_lower for word in rt.split())]
            if risk_context:
                expansions.extend(risk_context[:3])
        for regulation in self.financial_keywords["regulations"]:
            if regulation.lower() in query_lower:
                expansions.append(f"{regulation} compliance")
        if expansions:
            return f"{query} ({' OR '.join(expansions)})"
        return query

    def _requires_multi_hop_reasoning(self, query: str) -> bool:
        """判断是否需要多跳推理"""
        multi_hop_indicators = ["compare", "relationship", "impact", "cause", "effect", "correlation", "trend", "change", "difference", "connection"]
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in multi_hop_indicators)

    async def _multi_hop_retrieval(self, query: str, vectorstore: FAISS, initial_docs: List[Document]) -> List[Document]:
        """多跳检索"""
        key_concepts = await self._extract_key_concepts_from_docs(initial_docs)
        additional_docs = []
        for concept in key_concepts[:3]:
            concept_query = f"{concept} {query}"
            concept_docs = await asyncio.to_thread(vectorstore.similarity_search, concept_query, k=3)
            additional_docs.extend(concept_docs)
        all_docs = initial_docs + additional_docs
        return self._deduplicate_documents(all_docs)[:self.config["rerank_top_k"]]

    async def _extract_key_concepts_from_docs(self, docs: List[Document]) -> List[str]:
        """从文档中提取关键概念"""
        key_concepts = []
        for doc in docs[:3]:
            content_lower = doc.page_content.lower()
            for category, terms in self.financial_keywords.items():
                for term in terms:
                    if term in content_lower:
                        key_concepts.append(term)
        concept_counts = Counter(key_concepts)
        return [concept for concept, count in concept_counts.most_common(5)]

    async def _generate_dynamic_prompt(self, query: str, documents: List[Document]) -> ChatPromptTemplate:
        """动态生成提示词"""
        query_type = self._classify_query_type(query)
        doc_types = [doc.metadata.get("chunk_type", "general") for doc in documents]
        dominant_doc_type = Counter(doc_types).most_common(1)[0][0] if doc_types else "general"
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
        相关文档：{context}
        用户问题：{question}
        回答要求：
        """
        if query_type == "risk_analysis":
            base_template += "- 重点分析风险类型、严重程度和潜在影响\n- 引用具体的风险因素和数据\n- 评估风险的可控性和缓解措施\n- 如果涉及监管风险，请明确相关法规条款\n"
        elif query_type == "compliance":
            base_template += "- 明确指出相关的监管要求和合规状态\n- 引用具体的法规条款（如SOX 404、SEC Item 105等）\n- 分析合规缺陷的严重性和整改要求\n- 评估对业务运营的影响\n"
        elif query_type == "financial_analysis":
            base_template += "- 提供具体的财务数据和指标\n- 分析财务趋势和变化原因\n- 评估对公司财务健康状况的影响\n- 如有同比数据，请进行对比分析\n"
        elif query_type == "comparison":
            base_template += "- 进行详细的对比分析\n- 突出显示关键差异和相似点\n- 分析差异的原因和影响\n- 提供数据支持的结论\n"
        else:
            base_template += "- 提供准确、具体的回答\n- 引用相关的文档内容作为依据\n- 如果信息不足，请明确说明\n- 保持客观和专业的分析角度\n"
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
        context = "\n\n".join([f"文档 {i+1}:\n{doc.page_content}" for i, doc in enumerate(documents[:5])])
        try:
            chain = prompt | self.llm | StrOutputParser()
            answer = await asyncio.to_thread(chain.invoke, {"context": context, "question": query})
            return answer.strip()
        except Exception as e:
            print(f"答案生成失败: {e}")
            return "抱歉，在生成答案时遇到了问题。请尝试重新表述您的问题。"

    async def _post_process_answer(self, answer: str, query: str, documents: List[Document]) -> str:
        """答案后处理"""
        verified_answer = await self._verify_facts(answer, documents)
        formatted_answer = self._format_answer(verified_answer)
        if self._requires_disclaimer(query):
            formatted_answer += "\n\n⚠️ 免责声明：本分析基于提供的文档内容，仅供参考。具体决策请咨询专业顾问。"
        return formatted_answer

    async def _verify_facts(self, answer: str, documents: List[Document]) -> str:
        """验证答案中的事实"""
        numbers = re.findall(r'\d+(?:\.\d+)?%?', answer)
        all_doc_content = " ".join([doc.page_content for doc in documents])
        verified_numbers = [num for num in numbers if num in all_doc_content]
        verification_ratio = len(verified_numbers) / len(numbers) if numbers else 1.0
        if verification_ratio < 0.5:
            answer = f"⚠️ 部分信息可能需要进一步验证\n\n{answer}"
        return answer

    def _format_answer(self, answer: str) -> str:
        """格式化答案"""
        formatted = answer
        if len(formatted) > 500:
            formatted = re.sub(r'。([^。]{100,})', r'。\n\n\1', formatted)
        return formatted

    def _requires_disclaimer(self, query: str) -> bool:
        """判断是否需要添加免责声明"""
        disclaimer_triggers = ["investment", "invest", "buy", "sell", "recommendation", "advice", "should", "suggest", "recommend"]
        query_lower = query.lower()
        return any(trigger in query_lower for trigger in disclaimer_triggers)

    def _calculate_confidence(self, query: str, documents: List[Document], answer: str) -> float:
        """计算答案置信度"""
        confidence = 0.0
        doc_quality = np.mean([doc.metadata.get("rerank_score", 0.5) for doc in documents])
        confidence += doc_quality * 0.4
        answer_completeness = min(len(answer) / 500, 1.0)
        confidence += answer_completeness * 0.2
        query_terms = set(query.lower().split())
        answer_terms = set(answer.lower().split())
        keyword_match = len(query_terms.intersection(answer_terms)) / len(query_terms)
        confidence += keyword_match * 0.2
        doc_count_score = min(len(documents) / 5, 1.0)
        confidence += doc_count_score * 0.1
        has_specific_data = bool(re.search(r'\d+(?:\.\d+)?[%$]?', answer))
        if has_specific_data:
            confidence += 0.1
        return min(confidence, 1.0)

    def _generate_citations(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """生成引用信息"""
        citations = []
        for i, doc in enumerate(documents):
            citation = {"id": i + 1, "content_preview": doc.page_content[:150] + "...", "relevance_score": doc.metadata.get("rerank_score", 0), "document_type": doc.metadata.get("chunk_type", "unknown"), "metadata": {k: v for k, v in doc.metadata.items() if k in ["document_index", "chunk_index", "importance_score"]}}
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
            explanation = await asyncio.to_thread(chain.invoke, {"query": query, "answer": answer[:500], "doc_count": len(documents)})
            return explanation.strip()
        except Exception as e:
            print(f"解释生成失败: {e}")
            return f"基于 {len(documents)} 个相关文档片段生成的答案"

async def test_advanced_rag():
    """测试高级RAG系统"""
    rag_service = AdvancedRAGService()
    test_documents = [
        "公司面临的主要风险包括市场风险、信用风险和操作风险。市场风险主要来自利率变化和汇率波动，预计可能导致年度收益下降5-10%。",
        "根据SOX 404条款要求，公司建立了内部控制制度。但在2023年度审计中发现了一项重大缺陷，涉及收入确认流程。",
        "公司的流动性比率为1.5，债务权益比为0.8。现金流量表显示经营活动现金流为正，但投资活动现金流为负。"
    ]
    test_metadata = [{"document_type": "10-K", "section": "Risk Factors"}, {"document_type": "10-K", "section": "Internal Controls"}, {"document_type": "10-K", "section": "Financial Statements"}]
    print("🔄 构建向量数据库...")
    vectorstore = await rag_service.build_enhanced_vectorstore(test_documents, test_metadata, save_path="test_vectorstore")
    test_queries = ["公司面临哪些主要风险？", "SOX合规状况如何？", "公司的财务状况是否健康？", "市场风险对公司的影响有多大？"]
    for query in test_queries:
        print(f"\n🔍 测试查询：{query}")
        result = await rag_service.intelligent_qa(query, vectorstore)
        print(f"答案：{result['answer']}")
        print(f"置信度：{result['confidence_score']:.2f}")
        print(f"检索文档数：{result['documents_retrieved']}")
        print(f"处理时间：{result['processing_time']:.2f}秒")

if __name__ == "__main__":
    asyncio.run(test_advanced_rag())