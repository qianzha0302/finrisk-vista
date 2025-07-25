import json
import os
import logging
import aiofiles
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from ..utils.config import Config

class PDFProcessorService:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP
        )
        self.risk_keywords = ["risk", "uncertainty", "threat", "challenge", "exposure"]

    async def process_pdf(self, file_path: str, document_id: str, metadata: dict) -> dict:
        """Process a PDF document into paragraphs."""
        try:
            loader = PyPDFLoader(file_path)
            pages = await loader.aload()
            paragraphs = []
            for page in pages:
                chunks = self.text_splitter.split_text(page.page_content)
                for chunk in chunks:
                    if any(keyword.lower() in chunk.lower() for keyword in self.risk_keywords):
                        paragraphs.append({
                            "text": chunk,
                            "page": page.metadata.get("page", 0),
                            "metadata": metadata
                        })
            await self._save_processed_data(document_id, {"paragraphs": paragraphs, "metadata": metadata})
            return {"document_id": document_id, "paragraphs": paragraphs}
        except FileNotFoundError as e:
            logging.error(f"PDF file not found: {file_path}, error: {e}")
            raise
        except Exception as e:
            logging.error(f"Error processing PDF {file_path}: {e}")
            raise

    async def _save_processed_data(self, document_id: str, data: dict):
        """Save processed data to JSON."""
        storage_path = Path(Config.STORAGE_PATH) / f"{document_id}.json"
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(storage_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(data, indent=2, ensure_ascii=False))