import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import seaborn as sns
import logging
from pathlib import Path

class VisualizationService:
    def __init__(self):
        pass

    def generate_visualization(self, dfs_by_year: dict, visualization_type: str):
        """Generate specified visualization from dataframes."""
        try:
            if visualization_type == "trend":
                return self._compare_risk_trends(dfs_by_year)
            elif visualization_type == "heatmap":
                return self._plot_risk_heatmap(list(dfs_by_year.values())[0])
            elif visualization_type == "wordcloud":
                return self._generate_wordcloud(list(dfs_by_year.values())[0])
            else:
                raise ValueError(f"Unsupported visualization type: {visualization_type}")
        except KeyError as e:
            logging.error(f"Data key missing for visualization: {e}")
            raise
        except Exception as e:
            logging.error(f"Error generating visualization: {e}")
            raise

    def _compare_risk_trends(self, dfs_by_year):
        records = []
        for year, df in dfs_by_year.items():
            counts = df["risk_type_1"].value_counts()
            for risk_type, count in counts.items():
                records.append({"Year": str(year), "Risk Type": risk_type, "Count": count})
        trend_df = pd.DataFrame(records)
        fig = px.line(trend_df, x="Year", y="Count", color="Risk Type", markers=True, title="Risk Type Trend")
        fig.update_xaxes(type='category')
        output_path = Path("visualizations") / "risk_trend.html"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.write_html(str(output_path))
        return {"type": "trend", "path": str(output_path)}

    def _plot_risk_heatmap(self, df):
        pivot = pd.pivot_table(df, index="risk_type_1", columns="severity_1", aggfunc="size", fill_value=0)
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.heatmap(pivot, annot=True, fmt="d", cmap="Reds", ax=ax)
        ax.set_title("Risk Type vs Severity")
        output_path = Path("visualizations") / "risk_heatmap.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path)
        plt.close(fig)
        return {"type": "heatmap", "path": str(output_path)}

    def _generate_wordcloud(self, df, column="Paragraph"):
        text = " ".join(df[column].dropna())
        wordcloud = WordCloud(width=800, height=400, background_color="white").generate(text)
        output_path = Path("visualizations") / "wordcloud.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        wordcloud.to_file(output_path)
        return {"type": "wordcloud", "path": str(output_path)}