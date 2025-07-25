from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class PromptTemplate(BaseModel):
    id: str
    template: str
    description: Optional[str] = None

class RiskAnalysisRequest(BaseModel):
    document_id: str
    selected_prompts: List[str]
    custom_prompts: Optional[Dict[str, str]] = None
    max_paragraphs: Optional[int] = 200

class RiskAnalysisResponse(BaseModel):
    analysis_id: str
    document_id: str
    results: List[Dict]
    summary_statistics: Dict
    processing_time: float