"""Compatibility import for the JobOps LLM client.

Application code should import from app.integrations.llm_api. Importing this
module has no network side effects.
"""

from app.integrations.llm_api import LLMAnalysis, LLMAnalysisError, analyze_with_llm

__all__ = ["LLMAnalysis", "LLMAnalysisError", "analyze_with_llm"]
