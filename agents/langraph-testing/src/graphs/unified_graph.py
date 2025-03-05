"""
Unified graph implementation for the test platform.
This graph uses composition instead of inheritance and provides multiple execution paths.
"""
from typing import Dict, Any, Optional, List, Callable, TypedDict, Type
from typing_extensions import NotRequired
import logging
from langgraph.graph import StateGraph, END

from ..config.graph_config import GraphConfig
from ..llm import LLMConfig, LLMProvider
from ..agents.test_executor import TestExecutorAgent
from ..agents.code_generator import PlaywrightCodeGenerator
from ..agents.parser import TestStepParser

logger = logging.getLogger(__name__)

class UnifiedGraph:
    """
    Unified graph for test execution with multiple execution paths.
    Uses composition instead of inheritance.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, llm_config: Optional[LLMConfig] = None):
        """
        Initialize the unified graph with components.
        
        Args:
            config: Optional configuration dictionary
            llm_config: Optional LLM configuration
        """
        self.config = config or {}
        self.llm_config = llm_config or LLMConfig.from_env()
        
        # Initialize components using composition
        self.parser = TestStepParser()
        self.test_executor = TestExecutorAgent(llm_config=self.llm_config)
        self.code_generator = PlaywrightCodeGenerator(llm_config=self.llm_config)
        
        # Initialize graph
        self._graph = None
        
        # Configure max retries
        self.max_retries = self.config.get("max_retries", 3)
    
    def get_state_class(self) -> Type:
        """
        Get the state class for the unified graph.
        
        Returns:
            A class definition for the graph state
        """
        class State(TypedDict):
            """State for unified test execution graph."""
            test_file: str
            steps: List[Dict[str, Any]]
            current_step: NotRequired[int]
            execution_mode: str
            generated_code: NotRequired[str]
            execution_result: NotRequired[Dict[str, Any]]
            results: List[Dict[str, Any]]
            retry_count: NotRequired[int]
            is_complete: bool
        
        return State
    
    def build_graph(self) -> StateGraph:
        """
        Build and return the unified graph with multiple execution paths.
        
        Returns:
            A configured StateGraph
        """
        # Initialize the graph with our state
        State = self.get_state_class()
        workflow = StateGraph(State)
        
        # Define node functions
        async def parse_test(state: Dict[str, Any]) -> Dict[str, Any]:
            """Parse the test file and determine execution mode."""
            steps = self.parser.parse_file(state["test_file"])
            return {
                "steps": steps,
                "results": [],
                "current_step": 0,
                "retry_count": 0,
                "is_complete": False
            }
        
        async def route_execution(state: Dict[str, Any]) -> Dict[str, Any]:
            """Determine which execution path to take."""
            # No changes to state, just routing
            return {}
        
        # Direct execution path
        async def execute_browser_step(state: Dict[str, Any]) -> Dict[str, Any]:
            """Execute a step using the browser agent."""
            steps = state["steps"]
            current_step = state["current_step"]
            results = state["results"].copy()
            
            if current_step >= len(steps):
                return {"is_complete": True}
            
            step = steps[current_step]
            result = await self.test_executor.execute_step(step)
            results.append(result)
            
            return {
                "results": results,
                "current_step": current_step + 1,
                "is_complete": not result.get("success", False) or current_step + 1 >= len(steps)
            }
        
        # Code generation path
        async def generate_code(state: Dict[str, Any]) -> Dict[str, Any]:
            """Generate Playwright code from test steps."""
            code = await self.code_generator.execute_steps(state["steps"])
            return {"generated_code": code.get("result", {}).get("output", "")}
        
        async def execute_code(state: Dict[str, Any]) -> Dict[str, Any]:
            """Execute the generated code."""
            code = state["generated_code"]
            result = await self.code_generator.execute_steps([{"action": "execute", "code": code}])
            
            # Check if execution failed and we should retry
            success = result.get("success", False)
            retry_count = state.get("retry_count", 0)
            
            if not success and retry_count < self.max_retries:
                return {
                    "execution_result": result,
                    "retry_count": retry_count + 1,
                    "is_complete": False
                }
            
            return {
                "execution_result": result,
                "is_complete": True
            }
        
        async def fix_code(state: Dict[str, Any]) -> Dict[str, Any]:
            """Fix the generated code based on execution results."""
            code = state["generated_code"]
            error = state.get("execution_result", {}).get("error", "Unknown error")
            
            # Create a prompt for fixing the code
            fix_prompt = f"""
            The following Playwright code failed with error: {error}
            
            Code:
            {code}
            
            Please fix the code to address this error.
            """
            
            # Use the code generator to fix the code
            fixed_code_result = await self.code_generator.execute_steps([
                {"action": "fix", "code": code, "error": error}
            ])
            
            fixed_code = fixed_code_result.get("result", {}).get("output", code)
            
            return {"generated_code": fixed_code}
        
        async def finalize(state: Dict[str, Any]) -> Dict[str, Any]:
            """Finalize the test execution."""
            # Clean up resources
            if hasattr(self.test_executor, "browser") and self.test_executor.browser:
                await self.test_executor.browser.stop()
            if hasattr(self.code_generator, "cleanup"):
                await self.code_generator.cleanup()
            
            return {"is_complete": True}
        
        # Add nodes to the graph
        workflow.add_node("parse_test", parse_test)
        workflow.add_node("route_execution", route_execution)
        workflow.add_node("execute_browser_step", execute_browser_step)
        workflow.add_node("generate_code", generate_code)
        workflow.add_node("execute_code", execute_code)
        workflow.add_node("fix_code", fix_code)
        workflow.add_node("finalize", finalize)
        
        # Add edges
        workflow.add_edge("parse_test", "route_execution")
        
        # Route based on execution mode
        workflow.add_conditional_edges(
            "route_execution",
            lambda state: "generate_code" if state["execution_mode"] == "CODE_GEN" else "execute_browser_step"
        )
        
        # Direct execution path
        workflow.add_conditional_edges(
            "execute_browser_step",
            lambda state: "finalize" if state["is_complete"] else "execute_browser_step"
        )
        
        # Code generation path
        workflow.add_edge("generate_code", "execute_code")
        workflow.add_conditional_edges(
            "execute_code",
            lambda state: (
                "finalize" if state["is_complete"] else 
                "fix_code"
            )
        )
        workflow.add_edge("fix_code", "execute_code")
        
        # Finalize to end
        workflow.add_edge("finalize", END)
        
        # Set the entrypoint
        workflow.set_entry_point("parse_test")
        
        return workflow
    
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
    
    async def run(self, test_file: str, execution_mode: str = "DIRECT") -> Dict[str, Any]:
        """
        Run the unified test execution graph.
        
        Args:
            test_file: Path to the test file
            execution_mode: Execution mode ("DIRECT" or "CODE_GEN")
            
        Returns:
            Results of the test execution
        """
        graph = self.get_graph()
        
        # Initialize state
        state = {
            "test_file": test_file,
            "execution_mode": execution_mode,
            "steps": [],
            "results": [],
            "is_complete": False
        }
        
        # Run the graph
        result = await graph.invoke(state)
        return result 