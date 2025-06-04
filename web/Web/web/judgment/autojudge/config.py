"""
Configuration for the auto-judge LLM system.
"""
import os
from typing import Dict, Any


DEFAULT_CONFIG = {
    "model": "gpt-4-turbo-preview",
    "temperature": 0.3,
    "max_tokens": 500,
    "user_prompt_template": "user_prompt.j2",
    "system_prompt_template": "system_prompt.j2"
}

# Alternative model configurations
MODEL_CONFIGS = {
    "gpt-4": {
        "model": "gpt-4",
        "temperature": 0.3,
        "max_tokens": 500
    },
    "gpt-4-turbo": {
        "model": "gpt-4-turbo-preview",
        "temperature": 0.3,
        "max_tokens": 500
    },
    "gpt-3.5": {
        "model": "gpt-3.5-turbo",
        "temperature": 0.3,
        "max_tokens": 400
    }
}


def get_llm_config() -> Dict[str, Any]:
    """
    Get the LLM configuration.
    
    Reads from environment variables and falls back to defaults.
    
    Returns:
        Dict containing LLM configuration
    """
    config = DEFAULT_CONFIG.copy()
    
    # Override with environment variables if present
    if os.environ.get('AUTOJUDGE_MODEL'):
        config['model'] = os.environ.get('AUTOJUDGE_MODEL')
    
    if os.environ.get('AUTOJUDGE_TEMPERATURE'):
        config['temperature'] = float(os.environ.get('AUTOJUDGE_TEMPERATURE'))
    
    if os.environ.get('AUTOJUDGE_MAX_TOKENS'):
        config['max_tokens'] = int(os.environ.get('AUTOJUDGE_MAX_TOKENS'))
    
    if os.environ.get('AUTOJUDGE_USER_PROMPT'):
        config['user_prompt_template'] = os.environ.get('AUTOJUDGE_USER_PROMPT')
    
    if os.environ.get('AUTOJUDGE_SYSTEM_PROMPT'):
        config['system_prompt_template'] = os.environ.get('AUTOJUDGE_SYSTEM_PROMPT')
    
    return config


def get_model_config(model_name: str) -> Dict[str, Any]:
    """
    Get configuration for a specific model.
    
    Args:
        model_name: Name of the model configuration
        
    Returns:
        Model configuration dict
    """
    base_config = get_llm_config()
    
    if model_name in MODEL_CONFIGS:
        base_config.update(MODEL_CONFIGS[model_name])
    
    return base_config