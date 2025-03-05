"""
Test executor agent for LangGraph workflow.
"""
from typing import Dict, List, Any, Optional
import asyncio
import os
import re
from langgraph.graph import StateGraph, END

from ..browser.browser_wrapper import BrowserUseWrapper
from ..parser import TestParser
from .parser import TestStepParser
from ..llm import LLMConfig, LLMProvider

class TestExecutorAgent:
    """
    Agent for executing test steps.
    """
    
    def __init__(self, api_key: Optional[str] = None, llm_config: Optional[LLMConfig] = None):
        """
        Initialize the test executor agent.
        
        Args:
            api_key: Optional API key (legacy, use llm_config instead)
            llm_config: Optional LLM configuration
        """
        # For backward compatibility with api_key
        if api_key and not llm_config:
            llm_config = LLMConfig(
                provider="anthropic",
                api_key=api_key,
                model="claude-3-sonnet-20240229"
            )
            
        self.llm_config = llm_config
        self.browser = BrowserUseWrapper(api_key=api_key, llm_config=llm_config)
        
        # Use the new TestStepParser instead of TestParser
        self.parser = TestStepParser()
    
    async def execute_test(self, test_file: str) -> List[Dict[str, Any]]:
        """
        Execute a test file.
        
        Args:
            test_file: Path to the test file
            
        Returns:
            List of test step results
        """
        # Parse the test file
        steps = self.parser.parse_file(test_file)
        
        # Start the browser
        await self.browser.start()
        
        # Execute each step
        results = []
        try:
            for step in steps:
                result = await self.browser.execute_step(step)
                results.append(result)
                
                # Stop execution if a step fails
                if not result.get("success", False):
                    break
        finally:
            # Always stop the browser
            await self.browser.stop()
        
        return results


def build_langgraph_workflow(api_key: Optional[str] = None, llm_config: Optional[LLMConfig] = None):
    """
    Build a LangGraph workflow for test execution.
    
    Args:
        api_key: Optional API key (legacy, use llm_config instead)
        llm_config: Optional LLM configuration
        
    Returns:
        LangGraph workflow
    """
    # If api_key is provided but no llm_config, create a default Anthropic config
    if api_key and not llm_config:
        llm_config = LLMConfig(
            provider="anthropic",
            api_key=api_key,
            model="claude-3-sonnet-20240229",
            temperature=0.0
        )
    
    # Create the agent
    executor = TestExecutorAgent(api_key=api_key, llm_config=llm_config)
    
    # Define the state structure
    class State:
        test_file: str
        steps: List[Dict[str, Any]]
        current_step: int
        results: List[Dict[str, Any]]
        is_complete: bool
    
    # Initialize the graph
    workflow = StateGraph(State)
    
    # Define the agent nodes
    async def parse_test(state):
        """Parse the test file."""
        steps = executor.parser.parse_file(state["test_file"])
        return {"steps": steps, "current_step": 0, "results": []}
    
    async def execute_step(state):
        """Execute the current test step."""
        current_step = state["current_step"]
        steps = state["steps"]
        
        if current_step >= len(steps):
            return {"is_complete": True}
        
        step = steps[current_step]
        result = await executor.browser.execute_step(step)
        
        results = state["results"].copy()
        results.append(result)
        
        return {
            "results": results,
            "current_step": current_step + 1,
            "is_complete": not result.get("success", False) or current_step + 1 >= len(steps)
        }
    
    async def finalize_test(state):
        """Finalize the test execution."""
        await executor.browser.stop()
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
