"""
Stagehand-based tool for Playwright automation.
Provides a more AI-friendly interface to Playwright with act, extract, and observe APIs.
"""
import os
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class StagehandTool:
    """
    Stagehand-based tool for Playwright automation.
    Uses Stagehand's act, extract, and observe APIs for more robust browser automation.
    """
    
    def __init__(self, headless: bool = True, slow_mo: int = 100, timeout: int = 30000):
        """
        Initialize the Stagehand tool.
        
        Args:
            headless: Whether to run the browser in headless mode
            slow_mo: Delay between actions in milliseconds
            timeout: Default timeout in milliseconds
        """
        self.browser = None
        self.context = None
        self.page = None
        self.headless = headless
        self.slow_mo = slow_mo
        self.timeout = timeout
        
    async def start(self):
        """Start a new browser session with Stagehand."""
        try:
            # Import here to avoid dependency issues if Stagehand is not installed
            from playwright.async_api import async_playwright
            from stagehand import StagehandPage
            
            self._playwright = await async_playwright().start()
            self.browser = await self._playwright.chromium.launch(
                headless=self.headless,
                slow_mo=self.slow_mo
            )
            self.context = await self.browser.new_context(
                viewport={'width': 1280, 'height': 720}
            )
            
            # Create a regular Playwright page first
            playwright_page = await self.context.new_page()
            await playwright_page.set_default_timeout(self.timeout)
            
            # Wrap it with Stagehand
            self.page = StagehandPage(playwright_page)
            
            logger.info("Started browser session with Stagehand")
            return True
        except Exception as e:
            logger.error(f"Failed to start browser session: {str(e)}")
            return False
    
    async def navigate(self, url: str) -> Dict[str, Any]:
        """
        Navigate to a URL.
        
        Args:
            url: The URL to navigate to
            
        Returns:
            Dict with success status and any error message
        """
        try:
            await self.page.goto(url, wait_until='networkidle')
            logger.info(f"Navigated to {url}")
            return {"success": True, "message": f"Successfully navigated to {url}"}
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {str(e)}")
            return {"success": False, "message": str(e)}
    
    async def act(self, instruction: str) -> Dict[str, Any]:
        """
        Perform an action on the page using Stagehand's act API.
        
        Args:
            instruction: Natural language instruction for the action
            
        Returns:
            Dict with success status and any error message
        """
        try:
            result = await self.page.act(instruction)
            logger.info(f"Performed action: {instruction}")
            return {"success": True, "message": f"Successfully performed: {instruction}", "result": result}
        except Exception as e:
            logger.error(f"Failed to perform action '{instruction}': {str(e)}")
            return {"success": False, "message": str(e)}
    
    async def extract(self, instruction: str) -> Dict[str, Any]:
        """
        Extract data from the page using Stagehand's extract API.
        
        Args:
            instruction: Natural language instruction for data extraction
            
        Returns:
            Dict with success status, extracted data, and any error message
        """
        try:
            data = await self.page.extract(instruction)
            logger.info(f"Extracted data with instruction: {instruction}")
            return {"success": True, "data": data}
        except Exception as e:
            logger.error(f"Failed to extract data with '{instruction}': {str(e)}")
            return {"success": False, "message": str(e), "data": None}
    
    async def observe(self) -> Dict[str, Any]:
        """
        Observe the current page state using Stagehand's observe API.
        
        Returns:
            Dict with success status, observation data, and any error message
        """
        try:
            observation = await self.page.observe()
            logger.info("Observed page state")
            return {"success": True, "observation": observation}
        except Exception as e:
            logger.error(f"Failed to observe page state: {str(e)}")
            return {"success": False, "message": str(e), "observation": None}
    
    async def take_screenshot(self, path: Optional[str] = None) -> Dict[str, Any]:
        """
        Take a screenshot of the current page.
        
        Args:
            path: Optional path to save the screenshot
            
        Returns:
            Dict with success status and path to the screenshot
        """
        try:
            if not path:
                path = f"screenshot_{int(asyncio.get_event_loop().time())}.png"
            
            await self.page.screenshot(path=path)
            logger.info(f"Took screenshot: {path}")
            return {"success": True, "path": path}
        except Exception as e:
            logger.error(f"Failed to take screenshot: {str(e)}")
            return {"success": False, "message": str(e)}
    
    async def execute_steps(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute a sequence of test steps.
        
        Args:
            steps: List of test steps to execute
            
        Returns:
            List of results for each step
        """
        results = []
        
        for step in steps:
            step_type = step.get("action", "").lower()
            result = {"step": step, "success": False}
            
            try:
                if step_type == "navigate":
                    url = step.get("url", "")
                    nav_result = await self.navigate(url)
                    result.update(nav_result)
                
                elif step_type == "click":
                    element = step.get("element", "")
                    instruction = f"click {element}"
                    act_result = await self.act(instruction)
                    result.update(act_result)
                
                elif step_type == "type" or step_type == "fill":
                    element = step.get("element", "")
                    text = step.get("text", "")
                    instruction = f"type {text} in {element}"
                    act_result = await self.act(instruction)
                    result.update(act_result)
                
                elif step_type == "wait":
                    seconds = step.get("seconds", 1)
                    await asyncio.sleep(seconds)
                    result["success"] = True
                    result["message"] = f"Waited for {seconds} seconds"
                
                elif step_type == "verify":
                    verify_type = step.get("type", "")
                    if verify_type == "text_present":
                        text = step.get("text", "")
                        instruction = f"check if text '{text}' is present on the page"
                        extract_result = await self.extract(instruction)
                        result.update(extract_result)
                    elif verify_type == "element_visible":
                        element = step.get("element", "")
                        instruction = f"check if element '{element}' is visible"
                        extract_result = await self.extract(instruction)
                        result.update(extract_result)
                
                else:
                    # For any other step type, try to use act with the raw step text
                    instruction = str(step)
                    act_result = await self.act(instruction)
                    result.update(act_result)
                
            except Exception as e:
                result["success"] = False
                result["message"] = str(e)
            
            results.append(result)
        
        return results
    
    async def close(self):
        """Close the browser and clean up resources."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, '_playwright'):
                await self._playwright.stop()
            
            logger.info("Closed browser session")
            return {"success": True}
        except Exception as e:
            logger.error(f"Error closing browser session: {str(e)}")
            return {"success": False, "message": str(e)}


class StagehandInput(BaseModel):
    """Input schema for Stagehand tool."""
    instruction: str = Field(description="The instruction to perform with Stagehand")
    action_type: str = Field(description="Type of action: 'act', 'extract', 'observe', or 'navigate'")


def create_stagehand_tools() -> List[Any]:
    """
    Create a list of tools for Stagehand-based Playwright automation.
    
    Returns:
        List of tools for use with LangChain
    """
    from langchain.tools import Tool
    
    # Create a shared instance of StagehandTool
    stagehand_tool = StagehandTool()
    
    # Helper function to ensure browser is started
    async def ensure_browser_started():
        if stagehand_tool.browser is None:
            await stagehand_tool.start()
    
    # Tool for navigation
    async def navigate_to_url(url: str) -> str:
        """Navigate to a specific URL."""
        await ensure_browser_started()
        result = await stagehand_tool.navigate(url)
        return str(result)
    
    # Tool for performing actions
    async def perform_action(instruction: str) -> str:
        """Perform an action on the webpage using natural language."""
        await ensure_browser_started()
        result = await stagehand_tool.act(instruction)
        return str(result)
    
    # Tool for extracting data
    async def extract_data(instruction: str) -> str:
        """Extract data from the webpage using natural language."""
        await ensure_browser_started()
        result = await stagehand_tool.extract(instruction)
        return str(result)
    
    # Tool for observing the page
    async def observe_page() -> str:
        """Observe the current state of the webpage and suggest possible actions."""
        await ensure_browser_started()
        result = await stagehand_tool.observe()
        return str(result)
    
    # Tool for executing a sequence of steps
    async def execute_test_steps(steps_json: str) -> str:
        """Execute a sequence of test steps."""
        import json
        await ensure_browser_started()
        
        try:
            steps = json.loads(steps_json)
            results = await stagehand_tool.execute_steps(steps)
            return json.dumps(results, indent=2)
        except json.JSONDecodeError:
            return '{"error": "Invalid JSON format for steps"}'
    
    # Create the tools
    tools = [
        Tool(
            name="navigate_to_url",
            func=navigate_to_url,
            description="Navigate to a specific URL. Input should be a valid URL."
        ),
        Tool(
            name="perform_action",
            func=perform_action,
            description="Perform an action on the webpage using natural language. Examples: 'click the login button', 'type hello in the search box'."
        ),
        Tool(
            name="extract_data",
            func=extract_data,
            description="Extract data from the webpage using natural language. Examples: 'get the price of the product', 'find all links on the page'."
        ),
        Tool(
            name="observe_page",
            func=observe_page,
            description="Observe the current state of the webpage and get suggestions for possible actions."
        ),
        Tool(
            name="execute_test_steps",
            func=execute_test_steps,
            description="Execute a sequence of test steps provided as a JSON string."
        )
    ]
    
    return tools 