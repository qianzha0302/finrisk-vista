import networkx as nx
from pyvis.network import Network
import logging
from pathlib import Path

class GraphService:
    def __init__(self):
        pass  # 移除共享图实例

    async def generate_risk_graph(self, analysis_data: dict, company_name: str) -> dict:
        """Generate a risk graph from analysis data."""
        try:
            graph = nx.DiGraph()  # 每次创建新图
            graph.add_node(company_name, label=company_name, color="blue", size=30)
            for result in analysis_data.get("results", []):
                risk_type = result["analysis"].get("risk_type_1", "Unknown")
                specific_risk = result["analysis"].get("specific_risk", "Unknown")
                severity = result["analysis"].get("severity_1", "Medium")
                graph.add_node(risk_type, label=risk_type, color="orange", size=20)
                graph.add_node(specific_risk, label=specific_risk, color="red", size=15)
                graph.add_edge(company_name, risk_type, title="contains")
                graph.add_edge(risk_type, specific_risk, title=severity)
            net = Network(directed=True)
            net.from_nx(graph)
            output_path = Path("graphs") / f"{company_name}_risk_graph.html"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            net.write_html(str(output_path))
            return {"graph_path": str(output_path)}
        except FileNotFoundError as e:
            logging.error(f"Error writing graph file: {e}")
            raise
        except Exception as e:
            logging.error(f"Error generating risk graph: {e}")
            raise