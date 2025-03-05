"""
Custom tools for Playwright automation.
"""
import json
import logging
import requests
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from langchain.tools import BaseTool, Tool

logger = logging.getLogger(__name__)

class ExecuteCodeInput(BaseModel):
    """Input for executing Playwright code."""
    code: str = Field(description="The Playwright code to execute")

def create_playwright_tools(mcp_url: Optional[str] = None) -> List[BaseTool]:
    """
    Create tools for Playwright automation.
    
    Args:
        mcp_url: URL for the Playwright MCP service
        
    Returns:
        List of tools for Playwright automation
    """
    tools = []
    
    # Tool for executing Playwright code
    def execute_playwright_code(code: str) -> str:
        """Execute Playwright code via MCP service."""
        logger.info(f"Executing Playwright code: {code[:100]}...")
        
        if not mcp_url:
            return json.dumps({
                "success": False,
                "error": "No MCP URL provided. This is a simulation."
            })
        
        try:
            response = requests.post(
                f"{mcp_url}/execute",
                json={"code": code},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return json.dumps({
                    "success": True,
                    "result": result
                })
            else:
                return json.dumps({
                    "success": False,
                    "error": f"MCP service returned status code {response.status_code}: {response.text}"
                })
        except Exception as e:
            logger.error(f"Error executing Playwright code: {str(e)}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })
    
    execute_tool = Tool(
        name="execute_playwright_code",
        func=execute_playwright_code,
        description="Execute Playwright code to automate browser actions",
        args_schema=ExecuteCodeInput
    )
    tools.append(execute_tool)
    
    # Add more tools as needed
    
    return tools 