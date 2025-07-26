# services/pdf_processor.py
import json
import os
import time
import logging
import asyncio
import aiofiles
import re
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from ..utils.config import Config
from ..utils.rag_config import RAGConfig
from .rag_service import UnifiedRAGService

class PDFProcessorService:
    def __init__(self):
        # 使用RAG配置
        rag_config = RAGConfig.get_config()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=rag_config["chunk_size"],
            chunk_overlap=rag_config["chunk_overlap"],
            separators=["\n\n", "\n", ". ", "。", "；", ";", ":", "：", " "]
        )
        self.rag_service = UnifiedRAGService(config=rag_config)

    async def process_pdf(self, file_path: str, document_id: str, metadata: dict, save_vectorstore: bool = True, vectorstore_path: str = None) -> dict:
        """
        处理PDF文档，将全文分割成多个段落并构建RAG向量数据库
        - 完整解析PDF内容，不丢失任何信息
        - 智能分割成适合RAG的段落
        - 构建向量数据库用于后续查询
        """
        try:
            start_time = time.time()
            logging.info(f"🔄 开始处理PDF: {file_path}")

            # 1. 加载PDF文档
            loader = PyPDFLoader(file_path)
            pages = await asyncio.to_thread(loader.load)
            
            # 2. 合并所有页面内容
            full_text = ""
            page_info = []
            for i, page in enumerate(pages):
                page_content = page.page_content.strip()
                if page_content:  # 只处理非空页面
                    full_text += f"\n\n{page_content}"
                    page_info.append({
                        "page_number": i + 1,
                        "content_length": len(page_content),
                        "has_content": bool(page_content.strip())
                    })
            
            logging.info(f"📄 PDF加载完成: {len(pages)}页, 总字符数: {len(full_text)}")

            # 3. 智能段落分割 - 保持完整性
            documents = []
            document_metadata = []
            
            # 使用增强的文本分割器进行分割
            chunks = self.text_splitter.split_text(full_text)
            
            logging.info(f"📝 智能分割完成: {len(chunks)}个段落")
            
            # 4. 为每个段落添加丰富的元数据
            for i, chunk in enumerate(chunks):
                # 确定段落所属页面
                page_num = self._determine_page_number(chunk, pages)
                
                # 识别段落类型和重要性
                section_name = self._identify_section(chunk)
                chunk_importance = self._calculate_chunk_importance(chunk)
                
                # 提取关键信息
                key_entities = self._extract_key_entities(chunk)
                
                chunk_metadata = {
                    **metadata,
                    "chunk_index": i,
                    "page_number": page_num,
                    "section_name": section_name,
                    "importance_score": chunk_importance,
                    "word_count": len(chunk.split()),
                    "char_count": len(chunk),
                    "key_entities": key_entities,
                    "has_financial_data": self._has_financial_data(chunk),
                    "has_risk_content": self._has_risk_content(chunk),
                    "document_id": document_id,
                    "processed_at": time.time()
                }
                
                documents.append(chunk)
                document_metadata.append(chunk_metadata)

            # 5. 保存处理后的数据
            processed_data = {
                "document_id": document_id,
                "company_name": metadata.get("company", "Unknown"),
                "file_name": os.path.basename(file_path),
                "total_pages": len(pages),
                "total_chunks": len(documents),
                "processing_time": time.time() - start_time,
                "paragraphs": [
                    {"content": doc, "metadata": meta} 
                    for doc, meta in zip(documents, document_metadata)
                ],
                "page_info": page_info,
                "statistics": {
                    "total_words": sum(len(doc.split()) for doc in documents),
                    "total_chars": sum(len(doc) for doc in documents),
                    "avg_chunk_size": sum(len(doc) for doc in documents) / len(documents) if documents else 0,
                    "sections_identified": len(set(meta.get("section_name", "general") for meta in document_metadata)),
                    "high_importance_chunks": sum(1 for meta in document_metadata if meta.get("importance_score", 0) > 0.7)
                }
            }
            
            # 保存JSON文件
            storage_path = Path(Config.STORAGE_PATH) / f"{document_id}.json"
            storage_path.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(storage_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(processed_data, indent=2, ensure_ascii=False))

            logging.info(f"💾 数据保存完成: {len(documents)}个段落 -> {storage_path}")

            # 6. 构建RAG向量数据库
            if save_vectorstore:
                vectorstore_path = vectorstore_path or f"{Config.STORAGE_PATH}/{document_id}_vectorstore"
                
                logging.info(f"🔍 开始构建RAG向量数据库...")
                vectorstore = await self.rag_service.build_enhanced_vectorstore(
                    documents=documents,
                    document_metadata=document_metadata,
                    save_path=vectorstore_path
                )
                
                processed_data["vectorstore_path"] = vectorstore_path
                processed_data["vectorstore_built"] = True
                
                logging.info(f"✅ RAG向量数据库构建完成: {vectorstore_path}")
            else:
                processed_data["vectorstore_built"] = False

            total_time = time.time() - start_time
            logging.info(f"🎉 PDF处理完成! 总耗时: {total_time:.2f}秒")
            logging.info(f"📊 处理统计: {len(documents)}个段落, {processed_data['statistics']['total_words']}个单词")
            
            return processed_data

        except FileNotFoundError as e:
            logging.error(f"❌ PDF文件未找到: {file_path}, 错误: {e}")
            raise
        except Exception as e:
            logging.error(f"❌ 处理PDF {file_path} 时出错: {e}")
            raise

    async def query_pdf(self, document_id: str, query: str, vectorstore_path: str = None, conversation_history: list = None) -> dict:
        """
        对已处理的PDF执行RAG智能查询
        - 使用向量数据库检索相关段落
        - 通过LLM生成准确的答案
        - 支持多轮对话上下文
        """
        try:
            logging.info(f"🔍 开始RAG查询: {query[:50]}...")
            
            # 加载向量数据库
            vectorstore_path = vectorstore_path or f"{Config.STORAGE_PATH}/{document_id}_vectorstore"
            
            if not os.path.exists(vectorstore_path):
                raise FileNotFoundError(f"向量数据库不存在: {vectorstore_path}")
            
            vectorstore = await asyncio.to_thread(
                FAISS.load_local,
                vectorstore_path,
                self.rag_service.embedding_model
            )

            # 执行智能问答
            result = await self.rag_service.intelligent_qa(
                query=query, 
                vectorstore=vectorstore,
                conversation_history=conversation_history
            )
            
            # 添加文档信息
            result["document_id"] = document_id
            result["vectorstore_path"] = vectorstore_path
            
            logging.info(f"✅ RAG查询完成: '{query[:30]}...', 检索到 {result['documents_retrieved']} 个相关段落")
            return result

        except Exception as e:
            logging.error(f"❌ RAG查询失败 {document_id}: {e}")
            raise
    
    async def batch_query_pdf(self, document_id: str, queries: list, vectorstore_path: str = None) -> list:
        """批量查询处理"""
        results = []
        for query in queries:
            try:
                result = await self.query_pdf(document_id, query, vectorstore_path)
                results.append(result)
            except Exception as e:
                logging.error(f"批量查询失败 '{query}': {e}")
                results.append({
                    "query": query,
                    "error": str(e),
                    "answer": "查询处理失败"
                })
        return results

    def _determine_page_number(self, chunk: str, pages: list) -> int:
        """确定段落所属页面"""
        # 简单的启发式方法：查找包含chunk开头内容的页面
        chunk_start = chunk[:50].strip()
        for i, page in enumerate(pages):
            if chunk_start in page.page_content:
                return i + 1
        return 1  # 默认第一页
    
    def _identify_section(self, content: str) -> str:
        """识别文档章节类型"""
        content_lower = content.lower()
        
        # 风险因素
        if any(pattern in content_lower for pattern in ['item 1a', 'risk factor', 'risk management']):
            return "risk_factors"
        
        # 财务报表
        elif any(pattern in content_lower for pattern in ['balance sheet', 'income statement', 'cash flow', 'financial statement']):
            return "financial_statements"
        
        # 管理层讨论与分析
        elif any(pattern in content_lower for pattern in ['management discussion', 'md&a', 'liquidity', 'capital resources']):
            return "management_analysis"
        
        # 合规与内控
        elif any(pattern in content_lower for pattern in ['internal control', 'sox', 'compliance', 'audit']):
            return "compliance"
        
        # 业务概述
        elif any(pattern in content_lower for pattern in ['business overview', 'our business', 'products and services']):
            return "business_overview"
        
        # 市场信息
        elif any(pattern in content_lower for pattern in ['market', 'competition', 'industry']):
            return "market_info"
        
        return "general"
    
    def _calculate_chunk_importance(self, chunk: str) -> float:
        """计算段落重要性分数"""
        score = 0.0
        chunk_lower = chunk.lower()
        
        # 风险相关关键词
        risk_keywords = ['risk', 'uncertainty', 'threat', 'exposure', 'adverse', 'negative impact']
        for keyword in risk_keywords:
            if keyword in chunk_lower:
                score += 0.15
        
        # 财务关键词
        financial_keywords = ['revenue', 'profit', 'loss', 'assets', 'liabilities', 'capital', 'investment']
        for keyword in financial_keywords:
            if keyword in chunk_lower:
                score += 0.1
        
        # 监管关键词
        regulatory_keywords = ['sec', 'regulation', 'compliance', 'sox', 'gaap', 'ifrs']
        for keyword in regulatory_keywords:
            if keyword in chunk_lower:
                score += 0.12
        
        # 数字信息
        if re.search(r'\$[\d,]+', chunk) or re.search(r'\d+%', chunk):
            score += 0.1
        
        # 长度因子
        word_count = len(chunk.split())
        if 50 <= word_count <= 200:
            score += 0.1
        elif word_count > 200:
            score += 0.05
        
        return min(score, 1.0)
    
    def _extract_key_entities(self, chunk: str) -> dict:
        """提取关键实体"""
        entities = {
            "monetary_amounts": [],
            "percentages": [],
            "organizations": [],
            "dates": []
        }
        
        # 提取货币金额
        money_pattern = r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|thousand|M|B|K))?'
        entities["monetary_amounts"] = re.findall(money_pattern, chunk)[:5]
        
        # 提取百分比
        percent_pattern = r'\d+(?:\.\d+)?%'
        entities["percentages"] = re.findall(percent_pattern, chunk)[:5]
        
        # 提取年份
        year_pattern = r'\b(19|20)\d{2}\b'
        entities["dates"] = re.findall(year_pattern, chunk)[:5]
        
        return entities
    
    def _has_financial_data(self, chunk: str) -> bool:
        """检查是否包含财务数据"""
        financial_indicators = ['$', '%', 'revenue', 'profit', 'loss', 'assets', 'liabilities', 'million', 'billion']
        chunk_lower = chunk.lower()
        return any(indicator in chunk_lower for indicator in financial_indicators)
    
    def _has_risk_content(self, chunk: str) -> bool:
        """检查是否包含风险内容"""
        risk_indicators = ['risk', 'uncertainty', 'threat', 'exposure', 'adverse', 'challenge', 'volatility']
        chunk_lower = chunk.lower()
        return any(indicator in chunk_lower for indicator in risk_indicators)