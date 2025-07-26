# services/__init__.py
from typing import Dict, List, Any, Optional
from .pdf_processor import PDFProcessorService
from .risk_analyzer import RiskAnalyzerService
from .rag_service import AdvancedRAGService
from .graph_service import GraphService
from .export_service import ExportService
from .visualization_service import VisualizationService
from ..utils.rag_config import RAGConfig
from dotenv import load_dotenv
import os
import logging

# Load .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinRiskGPTServices:
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize FinRiskGPT services with configuration.
        
        Args:
            config: Optional custom configuration dictionary to override defaults.
        
        Raises:
            ValueError: If required configuration parameters are missing or services fail to initialize.
        """
        # Merge default and custom configuration
        self.config = {**RAGConfig.get_config(), **(config or {})}
        required_config = ['embedding_model', 'chunk_size', 'chunk_overlap', 'max_file_size_mb', 'template_path', 'storage_path', 'wkhtmltopdf_path']
        missing_params = [param for param in required_config if param not in self.config]
        if missing_params:
            logger.error(f"Missing required configuration parameters: {missing_params}")
            raise ValueError(f"Missing required configuration parameters: {missing_params}")

        # Initialize services with configuration
        try:
            self.pdf_processor = PDFProcessorService(config=self.config)
            self.risk_analyzer = RiskAnalyzerService(config=self.config)
            self.rag_service = AdvancedRAGService(config=self.config)
            self.graph_service = GraphService(config=self.config)
            self.export_service = ExportService(config=self.config)
            self.visualization_service = VisualizationService(config=self.config)
        except Exception as e:
            logger.error(f"Failed to initialize services: {str(e)}", exc_info=True)
            raise ValueError(f"Service initialization failed: {str(e)}")

        # Verify service initialization
        self._validate_services()

    def _validate_services(self):
        """Validate that all services are properly initialized."""
        services = {
            "pdf_processor": self.pdf_processor,
            "risk_analyzer": self.risk_analyzer,
            "rag_service": self.rag_service,
            "graph_service": self.graph_service,
            "export_service": self.export_service,
            "visualization_service": self.visualization_service
        }
        for service_name, service in services.items():
            if service is None or not hasattr(service, '__call__'):
                logger.warning(f"Service {service_name} is not properly initialized")
                raise ValueError(f"Service {service_name} initialization failed")

    async def process_document(self, file_path: str, document_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process a PDF document and return processed data.

        Args:
            file_path (str): Path to the PDF file.
            document_id (str): Unique identifier for the document.
            metadata (Dict[str, Any]): Metadata associated with the document.

        Returns:
            Dict[str, Any]: Processed document data.

        Raises:
            ValueError: If file path or metadata is invalid.
            Exception: If processing fails.
        """
        if not file_path or not os.path.exists(file_path):
            logger.error(f"Invalid file path: {file_path}")
            raise ValueError("File path is invalid or does not exist")
        if not isinstance(metadata, dict) or not all(key in metadata for key in ['user_id', 'document_type']):
            logger.error("Invalid metadata provided")
            raise ValueError("Metadata must include user_id and document_type")
        try:
            return await self.pdf_processor.process_pdf(file_path, document_id, metadata)
        except Exception as e:
            logger.error(f"Failed to process document {document_id}: {str(e)}", exc_info=True)
            raise

    async def analyze_risks(self, paragraphs: List[Dict[str, Any]], prompts: List[str], model_name: str = None) -> Dict[str, Any]:
        """Analyze risks in paragraphs using specified prompts.

        Args:
            paragraphs (List[Dict[str, Any]]): List of paragraph dictionaries with 'text' key.
            prompts (List[str]): List of prompt keys from PROMPT_REGISTRY.
            model_name (str, optional): Specific model to use. Defaults to None.

        Returns:
            Dict[str, Any]: Analysis results.

        Raises:
            ValueError: If paragraphs or prompts are invalid.
            Exception: If analysis fails.
        """
        if not paragraphs or not all(isinstance(p, dict) and "text" in p for p in paragraphs):
            logger.error("Invalid or empty paragraphs provided")
            raise ValueError("Paragraphs must be a non-empty list of dictionaries with 'text' key")
        if not prompts:
            logger.error("Empty prompts provided")
            raise ValueError("Prompts list cannot be empty")
        try:
            return await self.risk_analyzer.analyze_risks(paragraphs, prompts, model_name=model_name)
        except Exception as e:
            logger.error(f"Failed to analyze risks: {str(e)}", exc_info=True)
            raise

    async def query_document(self, question: str, document_id: str, user_id: str) -> Dict[str, Any]:
        """Query a document using RAG.

        Args:
            question (str): User query.
            document_id (str): Unique identifier for the document.
            user_id (str): User identifier for access control.

        Returns:
            Dict[str, Any]: Query response including answer and metadata.

        Raises:
            ValueError: If required parameters are missing.
            Exception: If query or vectorstore building fails.
        """
        if not question or not document_id or not user_id:
            logger.error("Missing required parameters for query")
            raise ValueError("Question, document_id, and user_id are required")
        try:
            vectorstore = await self.rag_service.get_or_build_vectorstore(document_id, user_id)
            return await self.rag_service.intelligent_qa(question, vectorstore)
        except Exception as e:
            logger.error(f"Failed to query document {document_id}: {str(e)}", exc_info=True)
            raise

    async def generate_risk_graph(self, analysis_data: Dict[str, Any], company_name: str) -> Dict[str, Any]:
        """Generate a risk graph from analysis data.

        Args:
            analysis_data (Dict[str, Any]): Risk analysis results.
            company_name (str): Name of the company for labeling.

        Returns:
            Dict[str, Any]: Graph data or configuration.

        Raises:
            ValueError: If analysis_data or company_name is invalid.
            Exception: If graph generation fails.
        """
        if not analysis_data or not company_name:
            logger.error("Invalid analysis_data or company_name")
            raise ValueError("Analysis data and company name are required")
        try:
            return await self.graph_service.generate_risk_graph(analysis_data, company_name)
        except Exception as e:
            logger.error(f"Failed to generate risk graph for {company_name}: {str(e)}", exc_info=True)
            raise

    async def generate_report(self, analysis_data: Dict[str, Any], export_type: str, user_id: str) -> str:
        """Generate a PDF or Excel report.

        Args:
            analysis_data (Dict[str, Any]): Data to include in the report.
            export_type (str): Type of export (e.g., 'pdf', 'excel').
            user_id (str): User identifier for personalization.

        Returns:
            str: Path to the generated report file.

        Raises:
            ValueError: If required parameters are missing.
            Exception: If report generation fails.
        """
        if not analysis_data or not export_type or not user_id:
            logger.error("Missing required parameters for report generation")
            raise ValueError("Analysis data, export type, and user_id are required")
        try:
            return await self.export_service.generate_pdf_report(analysis_data, export_type, user_id)
        except Exception as e:
            logger.error(f"Failed to generate report for user {user_id}: {str(e)}", exc_info=True)
            raise

    async def compare_models(self, paragraphs: List[Dict[str, Any]], prompts: List[str], models: List[str] = None) -> Dict[str, Any]:
        """Compare risk analysis across multiple models.

        Args:
            paragraphs (List[Dict[str, Any]]): List of paragraph dictionaries with 'text' key.
            prompts (List[str]): List of prompt keys from PROMPT_REGISTRY.
            models (List[str], optional): List of model names to compare. Defaults to None.

        Returns:
            Dict[str, Any]: Comparison results.

        Raises:
            ValueError: If paragraphs or prompts are invalid.
            Exception: If model comparison fails.
        """
        if not paragraphs or not all(isinstance(p, dict) and "text" in p for p in paragraphs):
            logger.error("Invalid or empty paragraphs provided")
            raise ValueError("Paragraphs must be a non-empty list of dictionaries with 'text' key")
        if not prompts:
            logger.error("Empty prompts provided")
            raise ValueError("Prompts list cannot be empty")
        try:
            return await self.multi_model_service.compare_models(paragraphs, prompts, models)
        except Exception as e:
            logger.error(f"Failed to compare models: {str(e)}", exc_info=True)
            raise

    async def generate_visualizations(self, dfs_by_year: Dict[str, Any], visualization_type: str) -> Any:
        """Generate visualizations (e.g., trend plots, heatmaps).

        Args:
            dfs_by_year (Dict[str, Any]): Dataframes organized by year.
            visualization_type (str): Type of visualization (e.g., 'trend', 'heatmap').

        Returns:
            Any: Visualization data or object.

        Raises:
            ValueError: If dfs_by_year or visualization_type is invalid.
            Exception: If visualization generation fails.
        """
        if not dfs_by_year or not visualization_type:
            logger.error("Invalid dfs_by_year or visualization_type")
            raise ValueError("Dataframes and visualization type are required")
        try:
            return await self.visualization_service.generate_visualization(dfs_by_year, visualization_type)
        except Exception as e:
            logger.error(f"Failed to generate visualization: {str(e)}", exc_info=True)
            raise

    async def check_service_health(self) -> Dict[str, bool]:
        """Check the health status of all services.
        
        Returns:
            Dict[str, bool]: Status of each service (True if healthy, False otherwise).
        """
        health_status = {}
        try:
            health_status["pdf_processor"] = hasattr(self.pdf_processor, 'process_pdf')
            health_status["risk_analyzer"] = hasattr(self.risk_analyzer, 'analyze_risks')
            health_status["rag_service"] = hasattr(self.rag_service, 'intelligent_qa')
            health_status["graph_service"] = hasattr(self.graph_service, 'generate_risk_graph')
            health_status["export_service"] = hasattr(self.export_service, 'generate_pdf_report')
            health_status["visualization_service"] = hasattr(self.visualization_service, 'generate_visualization')
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}", exc_info=True)
            for service in health_status:
                health_status[service] = False
        return health_status
