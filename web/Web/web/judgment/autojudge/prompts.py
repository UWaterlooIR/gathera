"""
Prompt management using Jinja2 templates.
"""
import os
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, Template


class PromptManager:
    """Manage prompt templates using Jinja2."""
    
    def __init__(self):
        """Initialize the Jinja2 environment."""
        self.prompts_dir = os.path.join(os.path.dirname(__file__), 'prompts')
        self.env = Environment(
            loader=FileSystemLoader(self.prompts_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def get_system_prompt(self, template_name: str = "system_prompt.j2") -> str:
        """
        Get the system prompt.
        
        Args:
            template_name: Name of the system prompt template
            
        Returns:
            Rendered system prompt
        """
        template = self.env.get_template(template_name)
        return template.render()
    
    def get_user_prompt(
        self,
        doc_title: str,
        doc_snippet: str,
        seed_query: str,
        topic_description: str,
        additional_context: Optional[Dict[str, Any]] = None,
        template_name: str = "user_prompt.j2"
    ) -> str:
        """
        Get the formatted user prompt for document judgment.
        
        Args:
            doc_title: Document title
            doc_snippet: Document snippet/content
            seed_query: The search query/topic
            topic_description: Description of the topic
            additional_context: Optional additional context
            template_name: Name of the user prompt template
            
        Returns:
            Rendered user prompt
        """
        template = self.env.get_template(template_name)
        
        return template.render(
            doc_title=doc_title,
            doc_snippet=doc_snippet,
            seed_query=seed_query,
            topic_description=topic_description,
            additional_context=additional_context or {}
        )
    
    def list_available_templates(self) -> Dict[str, list]:
        """
        List all available prompt templates.
        
        Returns:
            Dict with 'system' and 'user' template lists
        """
        templates = {
            'system': [],
            'user': []
        }
        
        for filename in os.listdir(self.prompts_dir):
            if filename.endswith('.j2'):
                if filename.startswith('system_'):
                    templates['system'].append(filename)
                elif filename.startswith('user_'):
                    templates['user'].append(filename)
        
        return templates


# Convenience function for backward compatibility
def get_judgment_prompt(
    doc_title: str,
    doc_snippet: str,
    seed_query: str,
    topic_description: str,
    additional_context: Optional[Dict[str, Any]] = None,
    prompt_style: str = "default"
) -> str:
    """
    Get the formatted prompt for document judgment.
    
    Args:
        doc_title: Document title
        doc_snippet: Document snippet/content
        seed_query: The search query/topic
        topic_description: Description of the topic
        additional_context: Optional additional context
        prompt_style: Style of prompt to use ('default' or 'strict')
        
    Returns:
        Formatted prompt string
    """
    manager = PromptManager()
    
    # Map prompt styles to template names
    template_map = {
        "default": "user_prompt.j2",
        "strict": "user_prompt_strict.j2"
    }
    
    template_name = template_map.get(prompt_style, "user_prompt.j2")
    
    return manager.get_user_prompt(
        doc_title=doc_title,
        doc_snippet=doc_snippet,
        seed_query=seed_query,
        topic_description=topic_description,
        additional_context=additional_context,
        template_name=template_name
    )