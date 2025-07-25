
# utils/database.py
import asyncio
import json
import sqlite3
import aiosqlite
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import hashlib
import uuid
import logging
import os

from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "finriskgpt.db"):
        self.db_path = db_path
        asyncio.create_task(self.initialize_database())

    async def initialize_database(self):
        """Initialize database schema"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id TEXT PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        hashed_password TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS documents (
                        id TEXT PRIMARY KEY,
                        user_id TEXT,
                        filename TEXT NOT NULL,
                        document_type TEXT,
                        company TEXT,
                        filing_date TEXT,
                        paragraphs_count INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_results (
                        id TEXT PRIMARY KEY,
                        document_id TEXT,
                        user_id TEXT,
                        results TEXT,
                        prompts_used TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (document_id) REFERENCES documents(id),
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)
                await db.commit()
            except Exception as e:
                logger.error(f"Database initialization failed: {repr(e)}")
                raise

    async def create_user(self, username: str, hashed_password: str) -> str:
        """Create a new user and return user ID"""
        user_id = hashlib.sha256(username.encode()).hexdigest()[:16]
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "INSERT INTO users (id, username, hashed_password) VALUES (?, ?, ?)",
                    (user_id, username, hashed_password)
                )
                await db.commit()
            except Exception as e:
                logger.error(f"Failed to create user {username}: {repr(e)}")
                raise
        return user_id

    async def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                cursor = await db.execute(
                    "SELECT id, hashed_password FROM users WHERE username = ?", (username,)
                )
                result = await cursor.fetchone()
                return {"id": result[0], "hashed_password": result[1]} if result else None
            except Exception as e:
                logger.error(f"Failed to get user {username}: {repr(e)}")
                raise

    async def store_document_metadata(self, document_id: str, user_id: str, **kwargs):
        """Store document metadata"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "INSERT INTO documents (id, user_id, filename, document_type, company, filing_date, paragraphs_count) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        document_id,
                        user_id,
                        kwargs.get("filename", ""),
                        kwargs.get("document_type", ""),
                        kwargs.get("company", ""),
                        kwargs.get("filing_date", ""),
                        kwargs.get("paragraphs_count", 0)
                    )
                )
                await db.commit()
            except Exception as e:
                logger.error(f"Failed to store document metadata for {document_id}: {repr(e)}")
                raise

    async def store_analysis_results(self, document_id: str, user_id: str, results: Dict, prompts_used: List[str]):
        """Store analysis results"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "INSERT INTO analysis_results (id, document_id, user_id, results, prompts_used) VALUES (?, ?, ?, ?, ?)",
                    (
                        str(uuid.uuid4()),
                        document_id,
                        user_id,
                        json.dumps(results),
                        json.dumps(prompts_used)
                    )
                )
                await db.commit()
            except Exception as e:
                logger.error(f"Failed to store analysis results for {document_id}: {repr(e)}")
                raise

    async def get_analysis_results(self, document_id: str, user_id: str) -> Optional[Dict]:
        """Get analysis results by document ID and user ID"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                cursor = await db.execute(
                    "SELECT results FROM analysis_results WHERE document_id = ? AND user_id = ?",
                    (document_id, user_id)
                )
                result = await cursor.fetchone()
                return json.loads(result[0]) if result else None
            except Exception as e:
                logger.error(f"Failed to get analysis results for {document_id}: {repr(e)}")
                raise

    async def get_user_analytics(self, user_id: str) -> Dict:
        """Get user analytics (e.g., number of documents, recent analyses)"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                cursor = await db.execute(
                    "SELECT COUNT(*) FROM documents WHERE user_id = ?",
                    (user_id,)
                )
                doc_count = (await cursor.fetchone())[0]
                return {"document_count": doc_count, "recent_analyses": []}  # Placeholder for recent analyses
            except Exception as e:
                logger.error(f"Failed to get analytics for user {user_id}: {repr(e)}")
                raise

