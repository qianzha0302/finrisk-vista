# services/pdf_processor.py
import json
import os
import logging
import aiofiles
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from ..utils.config import Config
from .rag_service import UnifiedRAGService  # 导入UnifiedRAGService

class PDFProcessorService:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP
        )
        self.rag_service = UnifiedRAGService()  # 初始化RAG服务

    async def process_pdf(self, file_path: str, document_id: str, metadata: dict, save_vectorstore: bool = False, vectorstore_path: str = None) -> dict:
        """处理PDF，分割成所有段落，构建RAG向量数据库"""
        try:
            start_time = time.time()
            logging.info(f"开始处理PDF: {file_path}")

            # 加载和分割PDF
            loader = PyPDFLoader(file_path)
            pages = await loader.aload()
            documents = []
            document_metadata = []
            for page in pages:
                chunks = self.text_splitter.split_text(page.page_content)
                section_name = self._identify_section(page.page_content) or metadata.get("section", "general")
                for chunk in chunks:
                    documents.append(chunk)
                    document_metadata.append({
                        **metadata,
                        "page_number": page.metadata.get("page", 0),
                        "section_name": section_name
                    })

            # 保存处理后的数据为JSON
            processed_data = {
                "document_id": document_id,
                "paragraphs": [
                    {"content": doc, "metadata": meta} for doc, meta in zip(documents, document_metadata)
                ]
            }
            storage_path = Path(Config.STORAGE_PATH) / f"{document_id}.json"
            storage_path.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(storage_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(processed_data, indent=2, ensure_ascii=False))

            logging.info(f"处理了 {len(documents)} 个片段，保存到 {storage_path}")

            # 构建RAG向量数据库
            vectorstore = None
            if save_vectorstore:
                vectorstore = await self.rag_service.build_enhanced_vectorstore(
                    documents=documents,
                    document_metadata=document_metadata,
                    save_path=vectorstore_path or f"{Config.STORAGE_PATH}/{document_id}_vectorstore"
                )
                processed_data["vectorstore_path"] = vectorstore_path or f"{Config.STORAGE_PATH}/{document_id}_vectorstore"
                logging.info(f"向量数据库构建完成，保存在 {processed_data['vectorstore_path']}")

            logging.info(f"PDF处理完成，总耗时 {time.time() - start_time:.2f}秒")
            return processed_data

        except FileNotFoundError as e:
            logging.error(f"PDF文件未找到: {file_path}, 错误: {e}")
            raise
        except Exception as e:
            logging.error(f"处理PDF {file_path} 时出错: {e}")
            raise

    async def query_pdf(self, document_id: str, query: str, vectorstore_path: str = None) -> dict:
        """对已处理的PDF执行RAG查询"""
        try:
            # 加载向量数据库
            vectorstore_path = vectorstore_path or f"{Config.STORAGE_PATH}/{document_id}_vectorstore"
            vectorstore = await asyncio.to_thread(
                FAISS.load_local,
                vectorstore_path,
                self.rag_service.embedding_model
            )

            # 执行查询
            result = await self.rag_service.intelligent_qa(query, vectorstore)
            logging.info(f"查询 '{query}' 完成，返回 {result['documents_retrieved']} 个相关文档")
            return result

        except Exception as e:
            logging.error(f"查询PDF {document_id} 时出错: {e}")
            raise

    def _identify_section(self, content: str) -> str:
        """识别文档章节"""
        section_patterns = [
            r'Item\s+1A\.?\s+Risk Factors',
            r'Management’s Discussion and Analysis',
            r'Financial Statements',
            r'Item\s+8\.?\s+Financial Statements'
        ]
        for pattern in section_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        return "general"
