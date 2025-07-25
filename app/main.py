
"""
FinRiskGPT Backend API
AI-Powered Financial Risk Analysis Assistant
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
import asyncio
import json
import os
import tempfile
import uuid
from datetime import datetime
import logging

# Import our custom modules
from models.risk_analysis import RiskAnalysisRequest, RiskAnalysisResponse, PromptTemplate
from models.rag_models import RAGQueryRequest, RAGQueryResponse
from models.graph_models import RiskGraphRequest, RiskGraphResponse
from services import InRiskGPTServices
from utils.auth import get_current_user, User
from utils.database import DatabaseManager
from utils.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="FinRiskGPT API",
    description="AI-Powered Financial Risk Analysis Assistant",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-lovable-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
services = InRiskGPTServices()
db_manager = DatabaseManager()

# Global state for background tasks
background_tasks_status = {}

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    paragraphs_extracted: int
    processing_status: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str  # "pending", "processing", "completed", "failed"
    progress: float
    result: Optional[Dict[Any, Any]] = None
    error_message: Optional[str] = None

# ==================== HEALTH CHECK ====================
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        timestamp=datetime.now().isoformat()
    )

# ==================== DOCUMENT PROCESSING ====================
@app.post("/api/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Query("10-K", description="Type of document"),
    company: str = Query("Unknown", description="Company name"),
    filing_date: str = Query("", description="Filing date"),
    current_user: User = Depends(get_current_user)
):
    """Upload and process PDF document"""
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Process PDF
        extracted_data = await services.process_document(
            tmp_file_path,
            document_id=document_id,
            metadata={
                "document_type": document_type,
                "company": company,
                "filing_date": filing_date,
                "user_id": current_user.id
            }
        )
        
        # Clean up temporary file
        os.unlink(tmp_file_path)
        
        # Store document metadata in database
        await db_manager.store_document_metadata(
            document_id=document_id,
            user_id=current_user.id,
            filename=file.filename,
            document_type=document_type,
            company=company,
            filing_date=filing_date,
            paragraphs_count=len(extracted_data['paragraphs'])
        )
        
        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            paragraphs_extracted=len(extracted_data['paragraphs']),
            processing_status="completed"
        )
        
    except Exception as e:
        logger.error(f"Document upload failed: {repr(e)}")
        raise HTTPException(status_code=500, detail=f"Document processing failed: {repr(e)}")

@app.get("/api/documents/{document_id}/paragraphs")
async def get_document_paragraphs(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get extracted paragraphs from a document"""
    try:
        paragraphs = await services.pdf_processor.get_document_paragraphs(document_id, current_user.id)
        return {"document_id": document_id, "paragraphs": paragraphs}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Document not found: {repr(e)}")

# ==================== RISK ANALYSIS ====================
@app.post("/api/analysis/risk", response_model=Dict[str, str])
async def start_risk_analysis(
    request: RiskAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Start risk analysis for a document"""
    task_id = str(uuid.uuid4())
    
    # Initialize task status
    background_tasks_status[task_id] = {
        "status": "pending",
        "progress": 0.0,
        "result": None,
        "error_message": None
    }
    
    # Start background analysis
    background_tasks.add_task(
        run_risk_analysis_task,
        task_id,
        request,
        current_user.id
    )
    
    return {"task_id": task_id, "status": "started"}

async def run_risk_analysis_task(task_id: str, request: RiskAnalysisRequest, user_id: str):
    """Background task for risk analysis"""
    try:
        background_tasks_status[task_id]["status"] = "processing"
        
        # Get document paragraphs
        paragraphs = await services.pdf_processor.get_document_paragraphs(request.document_id, user_id)
        
        # Run analysis with selected prompts
        results = await services.analyze_risks(
            paragraphs=paragraphs,
            prompts=request.selected_prompts,
            model_name=None
        )
        
        # Store results
        await db_manager.store_analysis_results(
            document_id=request.document_id,
            user_id=user_id,
            results=results,
            prompts_used=request.selected_prompts
        )
        
        background_tasks_status[task_id]["status"] = "completed"
        background_tasks_status[task_id]["progress"] = 100.0
        background_tasks_status[task_id]["result"] = results
        
    except Exception as e:
        logger.error(f"Risk analysis task {task_id} failed: {repr(e)}")
        background_tasks_status[task_id]["status"] = "failed"
        background_tasks_status[task_id]["error_message"] = repr(e)

def update_task_progress(task_id: str, progress: float):
    """Update task progress"""
    if task_id in background_tasks_status:
        background_tasks_status[task_id]["progress"] = progress

@app.get("/api/analysis/status/{task_id}", response_model=TaskStatusResponse)
async def get_analysis_status(task_id: str):
    """Get status of analysis task"""
    if task_id not in background_tasks_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    status_data = background_tasks_status[task_id]
    return TaskStatusResponse(
        task_id=task_id,
        status=status_data["status"],
        progress=status_data["progress"],
        result=status_data["result"],
        error_message=status_data.get("error_message")
    )

# ==================== PROMPT MANAGEMENT ====================
@app.get("/api/prompts/templates")
async def get_prompt_templates():
    """Get available prompt templates"""
    return {
        "templates": ENHANCED_PROMPT_REGISTRY,
        "total_count": len(ENHANCED_PROMPT_REGISTRY)
    }

@app.post("/api/prompts/custom")
async def save_custom_prompt(
    prompt_data: PromptTemplate,
    current_user: User = Depends(get_current_user)
):
    """Save custom prompt template"""
    try:
        # Note: db_manager.store_custom_prompt is not implemented yet
        # Placeholder implementation
        await db_manager.store_analysis_results(
            document_id="custom_prompt_" + prompt_data.id,
            user_id=current_user.id,
            results={"prompt": prompt_data.dict()},
            prompts_used=["custom"]
        )
        return {"status": "success", "prompt_id": prompt_data.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save prompt: {repr(e)}")

# ==================== RAG QUERIES ====================
@app.post("/api/rag/query", response_model=RAGQueryResponse)
async def rag_query(
    request: RAGQueryRequest,
    current_user: User = Depends(get_current_user)
):
    """Query documents using RAG"""
    try:
        response = await services.query_document(
            question=request.question,
            document_id=request.document_id,
            user_id=current_user.id
        )
        return response
    except Exception as e:
        logger.error(f"RAG query failed: {repr(e)}")
        raise HTTPException(status_code=500, detail=f"RAG query failed: {repr(e)}")

@app.post("/api/rag/vectorstore/build")
async def build_vectorstore(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Build vector store for document"""
    try:
        await services.rag_service.build_vectorstore_for_document(document_id, current_user.id)
        return {"status": "success", "message": "Vector store built successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector store build failed: {repr(e)}")

# ==================== RISK GRAPHS ====================
@app.post("/api/graph/generate", response_model=RiskGraphResponse)
async def generate_risk_graph(
    request: RiskGraphRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate risk knowledge graph"""
    try:
        # Get analysis results
        analysis_data = await db_manager.get_analysis_results(
            request.document_id,
            current_user.id
        )
        
        # Generate graph
        graph_data = await services.generate_risk_graph(
            analysis_data=analysis_data,
            company_name=request.company_name
        )
        
        return RiskGraphResponse(
            graph_html=graph_data["html"],
            nodes_count=graph_data["nodes_count"],
            edges_count=graph_data["edges_count"],
            graph_metadata=graph_data["metadata"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph generation failed: {repr(e)}")

# ==================== MULTI-MODEL COMPARISON ====================
@app.post("/api/analysis/multi-model")
async def multi_model_analysis(
    request: RiskAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """Run analysis using multiple models for comparison"""
    try:
        paragraphs = await services.pdf_processor.get_document_paragraphs(request.document_id, current_user.id)
        
        results = await services.compare_models(
            paragraphs=paragraphs,
            prompts=request.selected_prompts,
            models=["gpt-4o", "claude-3-sonnet", "gemini-pro"]
        )
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multi-model analysis failed: {repr(e)}")

# ==================== EXPORT SERVICES ====================
@app.post("/api/export/pdf")
async def export_pdf(
    document_id: str,
    export_type: str = Query("summary", description="Type of export: summary, full, custom"),
    current_user: User = Depends(get_current_user)
):
    """Export analysis results as PDF"""
    try:
        analysis_data = await db_manager.get_analysis_results(document_id, current_user.id)
        
        pdf_path = await services.generate_report(
            analysis_data=analysis_data,
            export_type=export_type,
            user_id=current_user.id
        )
        
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"risk_analysis_{document_id[:8]}.pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF export failed: {repr(e)}")

@app.post("/api/export/excel")
async def export_excel(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Export analysis results as Excel"""
    try:
        analysis_data = await db_manager.get_analysis_results(document_id, current_user.id)
        
        excel_path = await services.generate_report(
            analysis_data=analysis_data,
            export_type="excel",
            user_id=current_user.id
        )
        
        return FileResponse(
            excel_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"risk_analysis_{document_id[:8]}.xlsx"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Excel export failed: {repr(e)}")

# ==================== ANALYTICS & INSIGHTS ====================
@app.get("/api/analytics/dashboard")
async def get_dashboard_data(
    current_user: User = Depends(get_current_user)
):
    """Get dashboard analytics data"""
    try:
        dashboard_data = await db_manager.get_user_analytics(current_user.id)
        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard data fetch failed: {repr(e)}")

@app.get("/api/analytics/trends")
async def get_risk_trends(
    timeframe: str = Query("30d", description="Timeframe: 7d, 30d, 90d, 1y"),
    current_user: User = Depends(get_current_user)
):
    """Get risk trend analysis"""
    try:
        trends_data = await db_manager.get_risk_trends(current_user.id, timeframe)
        return trends_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trends data fetch failed: {repr(e)}")

# ==================== COMPLIANCE & REGULATORY ====================
@app.post("/api/compliance/audit")
async def compliance_audit(
    document_id: str,
    regulations: List[str] = Query(["SEC", "SOX", "FINRA"], description="Regulations to check"),
    current_user: User = Depends(get_current_user)
):
    """Run compliance audit on document"""
    try:
        paragraphs = await services.pdf_processor.get_document_paragraphs(document_id, current_user.id)
        
        audit_results = await services.analyze_risks(
            paragraphs=paragraphs,
            prompts=["compliance_audit_v2"],
            model_name=None
        )
        
        return audit_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compliance audit failed: {repr(e)}")

# ==================== WEBSOCKET FOR REAL-TIME UPDATES ====================
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"Message: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )