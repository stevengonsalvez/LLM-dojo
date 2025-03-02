"""
Graph configuration for the test platform.
"""
import os
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

class ExecutionMode(str, Enum):
    """Execution mode for the graph."""
    DIRECT = "DIRECT"
    CODE_GEN = "CODE_GEN"

@dataclass
class GraphConfig:
    """Configuration for the graph execution."""
    execution_mode: ExecutionMode = ExecutionMode.DIRECT
    playwright_mcp_url: Optional[str] = None
    enable_rag: bool = False
    verbose: bool = False
    max_retries: int = 3
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_env(cls) -> 'GraphConfig':
        """
        Create a GraphConfig instance from environment variables.
        
        Returns:
            Configured GraphConfig instance
        """
        # Get execution mode
        mode_str = os.getenv("EXECUTION_MODE", "DIRECT")
        execution_mode = ExecutionMode.DIRECT
        try:
            execution_mode = ExecutionMode[mode_str]
        except KeyError:
            # Default to DIRECT if invalid value
            pass
        
        # Get other configuration values
        playwright_mcp_url = os.getenv("PLAYWRIGHT_MCP_URL")
        enable_rag = os.getenv("ENABLE_RAG", "false").lower() == "true"
        verbose = os.getenv("VERBOSE", "false").lower() == "true"
        
        # Get max retries with fallback
        max_retries = 3
        max_retries_str = os.getenv("MAX_RETRIES")
        if max_retries_str:
            try:
                max_retries = int(max_retries_str)
            except ValueError:
                pass
        
        return cls(
            execution_mode=execution_mode,
            playwright_mcp_url=playwright_mcp_url,
            enable_rag=enable_rag,
            verbose=verbose,
            max_retries=max_retries
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the configuration to a dictionary.
        
        Returns:
            Dictionary representation of the configuration
        """
        result = {
            "execution_mode": self.execution_mode,
            "playwright_mcp_url": self.playwright_mcp_url,
            "enable_rag": self.enable_rag,
            "verbose": self.verbose,
            "max_retries": self.max_retries
        }
        
        # Include custom settings
        result.update(self.custom_settings)
        
        return result 