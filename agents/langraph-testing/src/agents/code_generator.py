"""
Code generator agent for Playwright automation.
"""
import os
import asyncio
import json
import logging
import requests
from typing import Dict, List, Any, Optional

from ..llm import LLMConfig, LLMProvider
from ..prompts.code_gen_prompts import CODE_GENERATION_PROMPT

logger = logging.getLogger(__name__)

class PlaywrightCodeGenerator:
    """
    Agent for generating Playwright code from test steps.
    """
    
    def __init__(self, llm_config: Optional[LLMConfig] = None, mcp_url: Optional[str] = None):
        """
        Initialize the code generator agent.
        
        Args:
            llm_config: Optional LLM configuration
            mcp_url: URL for the Playwright MCP service
        """
        # Initialize LLM provider
        self.llm_config = llm_config or LLMConfig.from_env()
        self.llm = LLMProvider.create(self.llm_config)
        
        # Set MCP URL
        self.mcp_url = mcp_url or os.getenv("PLAYWRIGHT_MCP_URL")
        if not self.mcp_url:
            logger.warning("Playwright MCP URL not provided, code execution will not be available")
    
    async def generate_code(self, test_steps: List[Dict[str, Any]]) -> str:
        """
        Generate Playwright code from test steps.
        
        Args:
            test_steps: List of parsed test steps
            
        Returns:
            Generated Playwright code
        """
        # Format the test steps for the prompt
        steps_text = "\n".join([f"{i+1}. {self._format_step(step)}" for i, step in enumerate(test_steps)])
        
        # Generate code using LLM
        prompt = CODE_GENERATION_PROMPT.format(test_steps=steps_text)
        
        try:
            code = await self.llm.generate(prompt)
            
            # Extract code block if present
            if "```" in code:
                # Extract content between first ``` and last ```
                code_parts = code.split("```")
                if len(code_parts) >= 3:
                    code = code_parts[1]
                    # Remove language identifier if present
                    if code.startswith("typescript") or code.startswith("javascript"):
                        code = code.split("\n", 1)[1]
            
            return code.strip()
        except Exception as e:
            logger.error(f"Error generating Playwright code: {str(e)}")
            raise
    
    async def execute_code(self, code: str) -> Dict[str, Any]:
        """
        Execute the generated Playwright code using the MCP service.
        
        Args:
            code: Generated Playwright code
            
        Returns:
            Execution results
        """
        if not self.mcp_url:
            return {
                "success": False,
                "error": "Playwright MCP URL not configured"
            }
        
        try:
            # Call the MCP service to execute the code
            response = requests.post(
                f"{self.mcp_url}/execute",
                json={"code": code},
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "result": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"MCP service returned status code {response.status_code}",
                    "response": response.text
                }
        except Exception as e:
            logger.error(f"Error executing Playwright code: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _format_step(self, step: Dict[str, Any]) -> str:
        """
        Format a test step for inclusion in the prompt.
        
        Args:
            step: Test step
            
        Returns:
            Formatted step text
        """
        action = step.get("action", "unknown")
        
        if action == "navigate":
            return f"Navigate to '{step.get('url', '')}'"
        elif action == "click":
            return f"Click on element '{step.get('element', '')}'"
        elif action == "hover":
            return f"Hover over element '{step.get('element', '')}'"
        elif action == "wait":
            return f"Wait for {step.get('seconds', 0)} seconds"
        elif action == "verify":
            verify_type = step.get("type", "")
            if verify_type == "text_present":
                return f"Verify text '{step.get('text', '')}' is present"
            elif verify_type == "element_visible":
                return f"Verify element '{step.get('element', '')}' is visible"
            else:
                return f"Verify: {json.dumps(step)}"
        else:
            return json.dumps(step) 