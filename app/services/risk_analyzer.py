# risk_analyzer.py
import json
import logging
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from ..utils.prompt_registry import PROMPT_REGISTRY, get_prompt_by_id
from ..utils.rag_config import RAGConfig
from dotenv import load_dotenv
import os
import asyncio
from typing import List, Dict

# 加载 .env 文件
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskAnalyzerService:
    def __init__(self):
        self.model = ChatOpenAI(
            model=RAGConfig.LLM_MODEL,
            api_key=os.getenv("OPENAI_API_KEY", RAGConfig.OPENAI_API_KEY)
        )
        self.output_parser = StrOutputParser()

    async def analyze_risks(self, paragraphs: List[Dict], prompts: List[str], model_name: str = None) -> Dict:
        """Analyze risks in paragraphs using specified prompts."""
        if not paragraphs or not prompts:
            logger.warning("Empty paragraphs or prompts provided")
            return {"results": []}

        try:
            model = ChatOpenAI(
                model=model_name or RAGConfig.LLM_MODEL,
                api_key=os.getenv("OPENAI_API_KEY", RAGConfig.OPENAI_API_KEY)
            )
            results = []
            tasks = []
            for prompt_key in prompts:
                prompt_config = get_prompt_by_id(prompt_key)  # 使用 get_prompt_by_id
                if not prompt_config:
                    logger.warning(f"Prompt {prompt_key} not found in registry")
                    continue
                chain = ChatPromptTemplate.from_template(prompt_config.template) | model | self.output_parser
                for para in paragraphs:
                    if not isinstance(para, dict) or "text" not in para:
                        logger.error(f"Invalid paragraph format: {para}")
                        continue
                    tasks.append(self._analyze_single_paragraph(chain, para, prompt_key))
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return {"results": [r for r in results if not isinstance(r, Exception)]}
        except Exception as e:
            logger.error(f"Error analyzing risks: {str(e)}", exc_info=True)
            raise

    async def _analyze_single_paragraph(self, chain, para: Dict, prompt_key: str) -> Dict:
        """Analyze a single paragraph."""
        try:
            raw_output = await chain.ainvoke({"paragraph": para["text"]})  # 使用 "paragraph" 作为键
            parsed = self._parse_output(raw_output, get_prompt_by_id(prompt_key))
            return {"paragraph": para["text"], "analysis": parsed, "prompt": prompt_key}
        except Exception as e:
            logger.error(f"Error analyzing paragraph: {str(e)}", exc_info=True)
            raise

    def _parse_output(self, raw_output: str, prompt_config) -> Dict:
        """Parse LLM output into structured format."""
        try:
            # 清理多余的 JSON 标记和换行
            cleaned_output = "\n".join(line.strip() for line in raw_output.splitlines() if line.strip())
            cleaned_output = cleaned_output.strip().strip("```json").strip("```")
            parsed = json.loads(cleaned_output)
            expected_fields = prompt_config.expected_output_schema.keys()
            return {field: parsed.get(field, "N/A") for field in expected_fields}
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {str(e)}, raw_output: {raw_output[:100]}...")
            return {
                "error": "Parse_Error",
                "raw_output": raw_output[:500],
                **{field: "N/A" for field in prompt_config.expected_output_schema.keys()}
            }
        except Exception as e:
            logger.error(f"Unexpected error parsing output: {str(e)}")
            return {"error": "Parse_Error", "raw_output": raw_output[:500]}