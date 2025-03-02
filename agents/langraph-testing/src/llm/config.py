"""
LLM configuration for the test platform.
"""
import os
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

@dataclass
class LLMConfig:
    """Configuration for the LLM provider."""
    
    provider: str
    api_key: str
    model: str
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    request_timeout: int = 60
    
    @classmethod
    def from_env(cls) -> 'LLMConfig':
        """Create an LLMConfig from environment variables."""
        # Log environment variables for debugging
        logger.info("Loading LLM configuration from environment variables")
        logger.info(f"LLM_PROVIDER: {os.getenv('LLM_PROVIDER')}")
        logger.info(f"LLM_MODEL: {os.getenv('LLM_MODEL')}")
        
        # Get API key based on provider
        provider = os.getenv('LLM_PROVIDER', 'anthropic')
        api_key = None
        
        if provider == 'anthropic':
            api_key = os.getenv('ANTHROPIC_API_KEY')
        elif provider == 'openai':
            api_key = os.getenv('OPENAI_API_KEY')
        elif provider == 'azure':
            api_key = os.getenv('AZURE_OPENAI_API_KEY')
        
        if not api_key:
            raise ValueError(f"API key for provider '{provider}' is not set in environment variables")
        
        # Create and return the config
        config = cls(
            provider=provider,
            api_key=api_key,
            model=os.getenv('LLM_MODEL', 'claude-3-sonnet-20240229' if provider == 'anthropic' else 'gpt-4'),
            temperature=float(os.getenv('LLM_TEMPERATURE', '0.1')),
            max_tokens=int(os.getenv('LLM_MAX_TOKENS')) if os.getenv('LLM_MAX_TOKENS') else None,
            request_timeout=int(os.getenv('LLM_REQUEST_TIMEOUT', '60')),
        )
        
        logger.info(f"Created LLM config with provider: {config.provider}, model: {config.model}")
        return config 