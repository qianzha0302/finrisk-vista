from pydantic import BaseModel
from typing import List, Optional

class RAGQueryRequest(BaseModel):
    document_id: str
    question: str
    top_k: int = 5
    prompt_type: Optional[str] = "default"

class RAGQueryResponse(BaseModel):
    question: str
    answer: str
    relevant_paragraphs: List[str]
    confidence_score: float