"""
LLM integration for auto-judging documents.
"""
import os
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from .prompts import PromptManager
from .config import get_llm_config

logger = logging.getLogger(__name__)


class LLMJudge:
    """Handle LLM-based document judgment."""
    
    def __init__(self):
        """Initialize the LLM client."""
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = OpenAI(api_key=api_key)
        self.config = get_llm_config()
        self.prompt_manager = PromptManager()
    
    def judge_document(
        self,
        doc_title: str,
        doc_snippet: str,
        seed_query: str,
        topic_description: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Judge a document's relevance using the LLM.
        
        Args:
            doc_title: The document title
            doc_snippet: The document snippet/content
            seed_query: The search query/topic
            topic_description: Description of the topic
            additional_context: Optional additional context
            
        Returns:
            Dict containing judgment results and LLM output
        """
        try:
            # Get the prompts
            system_prompt = self.prompt_manager.get_system_prompt()
            user_prompt = self.prompt_manager.get_user_prompt(
                doc_title=doc_title,
                doc_snippet=doc_snippet,
                seed_query=seed_query,
                topic_description=topic_description,
                additional_context=additional_context,
                template_name=self.config.get('user_prompt_template', 'user_prompt.j2')
            )
            
            # Call the LLM
            response = self.client.chat.completions.create(
                model=self.config['model'],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.config['temperature'],
                max_tokens=self.config['max_tokens']
            )
            
            # Extract the response
            llm_output = response.choices[0].message.content
            
            # Parse the judgment from the output
            judgment_result = self._parse_judgment(llm_output)
            
            return {
                "llm_output": llm_output,
                "judgment": judgment_result['judgment'],
                "confidence": judgment_result['confidence'],
                "overall_grade": judgment_result['overall_grade'],
                "reasoning": judgment_result['reasoning'],
                "tokens_used": response.usage.total_tokens,
                "model": self.config['model']
            }
            
        except Exception as e:
            logger.error(f"LLM judgment failed: {e}")
            raise
    
    def _parse_judgment(self, llm_output: str) -> Dict[str, Any]:
        """
        Parse the LLM output to extract judgment information.
        
        Args:
            llm_output: Raw output from the LLM
            
        Returns:
            Dict containing parsed judgment, confidence, and reasoning
        """
        # Default values
        result = {
            "judgment": "Not Useful",
            "confidence": -1,  # Default confidence
            "reasoning": llm_output,
            "overall_grade": "Unclear"  # Default overall grade
        }
        
        # Simple parsing logic - can be enhanced
        output_lower = llm_output.lower()
        
        # Look for relevance indicators
        if "not useful" in output_lower:
            result["judgment"] = "not_useful"
        elif "highly useful" in output_lower:
            result["judgment"] = "highly useful"
        elif "useful" in output_lower:
            result["judgment"] = "useful"
        
        # Extract confidence if mentioned
        import re
        confidence_match = re.search(r'confidence[:\s]+(\d+(?:\.\d+)?)', output_lower)
        if confidence_match:
            result["confidence"] = float(confidence_match.group(1))
            if result["confidence"] > 1:
                result["confidence"] = result["confidence"] / 100
        
        return result


def execute_llm_judgment(
    doc_title: str,
    doc_search_snippet: str,
    session: Any,
    seed_query: str,
    description: str
) -> Dict[str, Any]:
    """
    Execute LLM judgment for a document.
    
    This is the main entry point used by the AutoJudgmentAJAXView.
    
    Args:
        doc_title: Document title
        doc_search_snippet: Document snippet
        session: User session object
        seed_query: Seed query for the topic
        description: Topic description
        
    Returns:
        Dict containing LLM judgment results
    """
    judge = LLMJudge()
    
    # Additional context from session if needed
    additional_context = {
        "session_id": str(session.uuid) if hasattr(session, 'uuid') else None,
        "strategy": session.strategy if hasattr(session, 'strategy') else None,
    }
    
    return judge.judge_document(
        doc_title=doc_title,
        doc_snippet=doc_search_snippet,
        seed_query=seed_query,
        topic_description=description,
        additional_context=additional_context
    )