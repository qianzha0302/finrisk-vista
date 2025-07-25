from pydantic import BaseModel
from typing import Dict, Optional

class RiskGraphRequest(BaseModel):
    document_id: str
    company_name: str
    graph_type: str = "network"  # e.g., network, tree

class RiskGraphResponse(BaseModel):
    graph_html: str
    nodes_count: int
    edges_count: int
    graph_metadata: Optional[Dict] = None