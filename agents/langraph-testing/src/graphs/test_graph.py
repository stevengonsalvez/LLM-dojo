"""
Test execution graph using Browser-Use.
"""
from typing import Dict, List, Any, Optional, Callable, Type, Union
from langgraph.graph import StateGraph, END

from ..agents.test_executor import TestExecutorAgent
from ..llm import LLMConfig
from ..config.graph_config import GraphConfig
from .base_graph import BaseGraph

class TestGraph(BaseGraph):
    """Graph for direct test execution using Browser-Use."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, llm_config: Optional[LLMConfig] = None):
        """
        Initialize the test graph.
        
        Args:
            config: Optional configuration dictionary
            llm_config: Optional LLM configuration
        """
        super().__init__(config)
        self.llm_config = llm_config
        self.agent = TestExecutorAgent(llm_config=self.llm_config)
    
    @staticmethod
    def get_state_class() -> Type:
        """
        Get the state class for the graph.
        
        Returns:
            State class definition
        """
        from typing_extensions import TypedDict
        
        class State(TypedDict):
            """State for test execution graph."""
            test_file: str
            steps: List[Dict[str, Any]]
            current_step: int
            results: List[Dict[str, Any]]
            is_complete: bool
        
        return State
    
    def build_graph(self) -> StateGraph:
        """
        Build and return the test execution graph.
        
        Returns:
            Configured StateGraph
        """
        # Initialize the graph with our state
        State = self.get_state_class()
        workflow = StateGraph(State)
        
        # Define node functions
        async def parse_test(state: Dict[str, Any]) -> Dict[str, Any]:
            """Parse the test file."""
            steps = self.agent.parser.parse_file(state["test_file"])
            return {"steps": steps, "current_step": 0, "results": []}
        
        async def execute_step(state: Dict[str, Any]) -> Dict[str, Any]:
            """Execute the current test step."""
            current_step = state["current_step"]
            steps = state["steps"]
            
            if current_step >= len(steps):
                return {"is_complete": True}
            
            step = steps[current_step]
            result = await self.agent.browser.execute_step(step)
            
            results = state["results"].copy()
            results.append(result)
            
            return {
                "results": results,
                "current_step": current_step + 1,
                "is_complete": not result.get("success", False) or current_step + 1 >= len(steps)
            }
        
        async def finalize_test(state: Dict[str, Any]) -> Dict[str, Any]:
            """Finalize the test execution."""
            await self.agent.browser.stop()
            return {"is_complete": True}
        
        # Add nodes to the graph
        workflow.add_node("parse_test", parse_test)
        workflow.add_node("execute_step", execute_step)
        workflow.add_node("finalize", finalize_test)
        
        # Add conditional edges
        workflow.add_edge("parse_test", "execute_step")
        workflow.add_conditional_edges(
            "execute_step",
            lambda state: "finalize" if state["is_complete"] else "execute_step"
        )
        workflow.add_edge("finalize", END)
        
        # Set the entrypoint
        workflow.set_entry_point("parse_test")
        
        return workflow
    
    async def run(self, test_file: str) -> Dict[str, Any]:
        """
        Run the test execution graph.
        
        Args:
            test_file: Path to the test file
            
        Returns:
            Results of the test execution
        """
        graph = self.get_graph()
        
        # Create input state - in LangGraph 0.3.2, we need to pass a dictionary
        # that matches the state class structure, not create a State instance
        state = {"test_file": test_file}
        
        # Run the graph
        # For LangGraph 0.3.2, we need to use ainvoke for async functions
        result = await graph.ainvoke(state)
        return result 