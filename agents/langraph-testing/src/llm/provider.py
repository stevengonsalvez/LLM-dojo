"""
LLM provider abstraction for the test platform.
"""
import os
import logging
import importlib.util
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union

from .config import LLMConfig

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    """Base class for LLM providers."""
    
    def __init__(self, config: LLMConfig):
        """Initialize the LLM provider with config."""
        self.config = config
    
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Generate a response from the LLM."""
        pass
    
    @classmethod
    def create(cls, config: LLMConfig) -> 'LLMProvider':
        """Factory method to create the appropriate LLM provider."""
        if config.provider == 'anthropic':
            return AnthropicProvider(config)
        elif config.provider == 'openai':
            return OpenAIProvider(config)
        elif config.provider == 'azure':
            return AzureOpenAIProvider(config)
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")


class AnthropicProvider(LLMProvider):
    """Anthropic (Claude) provider implementation."""
    
    def __init__(self, config: LLMConfig):
        """Initialize the Anthropic provider."""
        super().__init__(config)
        
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=config.api_key)
            logger.info(f"Initialized Anthropic client with model {config.model}")
        except ImportError:
            logger.error("anthropic package not installed.")
            raise ImportError("Please install anthropic package: pip install anthropic")
    
    async def generate(self, prompt: str) -> str:
        """Generate a response using Anthropic Claude."""
        try:
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens or 1000,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.temperature
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Error generating with Anthropic: {str(e)}")
            raise


class OpenAIProvider(LLMProvider):
    """OpenAI provider implementation."""
    
    def __init__(self, config: LLMConfig):
        """Initialize the OpenAI provider."""
        super().__init__(config)
        
        try:
            import openai
            self.client = openai.OpenAI(api_key=config.api_key)
            logger.info(f"Initialized OpenAI client with model {config.model}")
        except ImportError:
            logger.error("openai package not installed.")
            raise ImportError("Please install openai package: pip install openai")
    
    async def generate(self, prompt: str) -> str:
        """Generate a response using OpenAI."""
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating with OpenAI: {str(e)}")
            raise


class AzureOpenAIProvider(LLMProvider):
    """Azure OpenAI provider implementation."""
    
    def __init__(self, config: LLMConfig):
        """Initialize the Azure OpenAI provider."""
        super().__init__(config)
        
        try:
            import openai
            
            # Azure OpenAI requires additional environment variables
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            if not azure_endpoint:
                raise ValueError("AZURE_OPENAI_ENDPOINT environment variable not set")
            
            self.client = openai.AzureOpenAI(
                api_key=config.api_key,
                api_version="2023-05-15",
                azure_endpoint=azure_endpoint
            )
            logger.info(f"Initialized Azure OpenAI client with model {config.model}")
        except ImportError:
            logger.error("openai package not installed.")
            raise ImportError("Please install openai package: pip install openai")
        except Exception as e:
            logger.error(f"Error initializing Azure OpenAI: {str(e)}")
            raise
    
    async def generate(self, prompt: str) -> str:
        """Generate a response using Azure OpenAI."""
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating with Azure OpenAI: {str(e)}")
            raise 