"""
Code generation graph using Playwright MCP tool.
"""
from typing import Dict, List, Any, Optional, Callable, Type, Union
from langgraph.graph import StateGraph, END

from ..agents.code_generator import PlaywrightCodeGenerator
from ..agents.parser import TestStepParser
from ..llm import LLMConfig
from ..config.graph_config import GraphConfig, ExecutionMode
from .base_graph import BaseGraph

class CodeGenGraph(BaseGraph):
    """Graph for test execution with code generation using Playwright."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, llm_config: Optional[LLMConfig] = None):
        """
        Initialize the code generation graph.
        
        Args:
            config: Optional configuration dictionary
            llm_config: Optional LLM configuration
        """
        super().__init__(config)
        self.llm_config = llm_config
        
        # Get MCP URL from config or use default
        mcp_url = None
        if config and "playwright_mcp_url" in config:
            mcp_url = config["playwright_mcp_url"]
        
        self.parser = TestStepParser()
        self.code_generator = PlaywrightCodeGenerator(
            llm_config=self.llm_config,
            mcp_url=mcp_url
        )
    
    @staticmethod
    def get_state_class() -> Type:
        """
        Get the state class for the graph.
        
        Returns:
            State class definition
        """
        from typing_extensions import TypedDict
        
        class State(TypedDict):
            """State for code generation graph."""
            test_file: str
            steps: List[Dict[str, Any]]
            generated_code: Optional[str]
            execution_result: Optional[Dict[str, Any]]
            results: List[Dict[str, Any]]
            is_complete: bool
        
        return State
    
    def build_graph(self) -> StateGraph:
        """
        Build and return the code generation graph.
        
        Returns:
            Configured StateGraph
        """
        # Initialize the graph with our state
        State = self.get_state_class()
        workflow = StateGraph(State)
        
        # Define node functions
        async def parse_test(state: Dict[str, Any]) -> Dict[str, Any]:
            """Parse the test file."""
            steps = self.parser.parse_file(state["test_file"])
            return {"steps": steps, "results": []}
        
        async def generate_code(state: Dict[str, Any]) -> Dict[str, Any]:
            """Generate Playwright code from test steps."""
            code = await self.code_generator.generate_code(state["steps"])
            return {"generated_code": code}
        
        async def execute_code(state: Dict[str, Any]) -> Dict[str, Any]:
            """Execute the generated code."""
            code = state["generated_code"]
            result = await self.code_generator.execute_code(code)
            
            return {
                "execution_result": result,
                "is_complete": True
            }
        
        # Add nodes to the graph
        workflow.add_node("parse_test", parse_test)
        workflow.add_node("generate_code", generate_code)
        workflow.add_node("execute_code", execute_code)
        
        # Add edges
        workflow.add_edge("parse_test", "generate_code")
        workflow.add_edge("generate_code", "execute_code")
        workflow.add_edge("execute_code", END)
        
        # Set the entrypoint
        workflow.set_entry_point("parse_test")
        
        return workflow
    
    async def run(self, test_file: str) -> Dict[str, Any]:
        """
        Run a test file through the code generation graph.
        
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