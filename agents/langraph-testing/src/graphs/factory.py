"""
Graph factory module for creating graph instances based on configuration.
"""
from typing import Dict, Any, Optional, Union

from ..config.graph_config import GraphConfig, ExecutionMode
from ..llm import LLMConfig
from .base_graph import BaseGraph
from .test_graph import TestGraph
from .code_gen_graph import CodeGenGraph
from .unified_graph import UnifiedGraph

def create_graph(
    config: Optional[Union[GraphConfig, Dict[str, Any]]] = None,
    llm_config: Optional[LLMConfig] = None,
    use_unified: bool = False
) -> Union[BaseGraph, UnifiedGraph]:
    """
    Create a graph instance based on the provided configuration.
    
    Args:
        config: Graph configuration, either as GraphConfig instance or dictionary
        llm_config: Optional LLM configuration
        use_unified: Whether to use the unified graph (composition-based) instead of inheritance-based graphs
        
    Returns:
        Configured graph instance
    """
    # Convert config to dictionary if it's a GraphConfig instance
    config_dict = None
    if config is not None:
        if isinstance(config, GraphConfig):
            config_dict = config.to_dict()
        else:
            config_dict = config
    
    # Use unified graph if specified
    if use_unified:
        return UnifiedGraph(config=config_dict, llm_config=llm_config)
            
    # Determine execution mode
    execution_mode = ExecutionMode.DIRECT
    if config_dict and "execution_mode" in config_dict:
        mode_value = config_dict["execution_mode"]
        # Handle both string and enum values
        if isinstance(mode_value, str):
            execution_mode = ExecutionMode[mode_value]
        else:
            execution_mode = mode_value
    
    # Create and return appropriate graph based on execution mode
    if execution_mode == ExecutionMode.CODE_GEN:
        return CodeGenGraph(config=config_dict, llm_config=llm_config)
    else:
        # Default to direct execution
        return TestGraph(config=config_dict, llm_config=llm_config) 