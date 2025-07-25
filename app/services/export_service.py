import os
import pandas as pd
import pdfkit
import logging
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from pathlib import Path
from ..utils.config import Config

class ExportService:
    def __init__(self):
        self.env = Environment(loader=FileSystemLoader(Config.TEMPLATE_PATH))

    async def generate_pdf_report(self, analysis_data: dict, export_type: str, user_id: str, visualizations: dict = None) -> str:
        """Generate a PDF report from analysis data."""
        try:
            df = pd.DataFrame(analysis_data.get("results", []))
            template = self.env.get_template(f"{export_type}_template.html")
            context = {
                "company_name": analysis_data.get("metadata", {}).get("company", "Unknown"),
                "results": df.to_dict(orient="records"),
                "visualizations": visualizations or {}
            }
            html_content = template.render(**context)
            output_path = Path("reports") / user_id / f"{export_type}_report.pdf"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            wkhtmltopdf_path = Path(Config.WKHTMLTOPDF_PATH)
            if not wkhtmltopdf_path.exists():
                raise FileNotFoundError(f"wkhtmltopdf not found at {wkhtmltopdf_path}")
            pdfkit.from_string(html_content, str(output_path), configuration=pdfkit.configuration(wkhtmltopdf=str(wkhtmltopdf_path)))
            return str(output_path)
        except TemplateNotFound as e:
            logging.error(f"Template not found: {export_type}_template.html, error: {e}")
            raise
        except FileNotFoundError as e:
            logging.error(f"File error generating PDF report: {e}")
            raise
        except Exception as e:
            logging.error(f"Error generating PDF report: {e}")
            raise