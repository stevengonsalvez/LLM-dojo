"""
Base graph implementation for the test platform.
"""
from typing import Dict, Any, Optional, Type
from abc import ABC, abstractmethod
from langgraph.graph import StateGraph

class BaseGraph(ABC):
    """Base class for all graphs in the test platform."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the graph with optional configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._graph = None
    
    @abstractmethod
    def build_graph(self) -> StateGraph:
        """
        Build and return the graph.
        
        Returns:
            A configured StateGraph
        """
        pass
    
    def get_graph(self) -> StateGraph:
        """
        Get the graph, building it if it hasn't been created yet.
        
        Returns:
            Built StateGraph
        """
        if self._graph is None:
            self._graph = self.build_graph()
            # Compile the graph before returning it
            self._graph = self._graph.compile()
        return self._graph
    
    @staticmethod
    def get_state_class() -> Type:
        """
        Get the state class for the graph.
        
        Returns:
            A class definition for the graph state
        """
        from typing_extensions import TypedDict
        
        class State(TypedDict, total=False):
            """Base state for graph execution."""
            pass
        
        return State 