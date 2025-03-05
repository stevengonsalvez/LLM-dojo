"""
Code generator agent for Playwright automation using LangChain.
"""
import os
import logging
import asyncio
from typing import Dict, List, Any, Optional
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic

from ..llm import LLMConfig, LLMProvider
from ..prompts.code_gen_prompts import (
    DEFAULT_PLAYWRIGHT_PROMPT,
    ACCESSIBILITY_TESTING_PROMPT,
    PERFORMANCE_TESTING_PROMPT
)
from ..tools.stagehand_tool import create_stagehand_tools, StagehandTool

logger = logging.getLogger(__name__)

class PlaywrightCodeGenerator:
    """
    Code generator for Playwright automation using LangChain.
    Uses Stagehand for more robust browser automation.
    """
    
    def __init__(
        self, 
        llm_config: Optional[LLMConfig] = None,
        prompt_template: Optional[str] = None,
        mcp_url: Optional[str] = None
    ):
        """
        Initialize the Playwright code generator.
        
        Args:
            llm_config: LLM configuration
            prompt_template: Custom prompt template (optional)
            mcp_url: URL for the Playwright MCP service (if using)
        """
        self.llm_config = llm_config or LLMConfig.from_env()
        
        # Use LangChain's ChatAnthropic directly instead of our custom provider
        if self.llm_config.provider == 'anthropic':
            self.llm = ChatAnthropic(model=self.llm_config.model)
        else:
            # Fallback to our custom provider for other models
            self.llm = LLMProvider.create(self.llm_config)
            
        # Initialize Stagehand tool
        self.browser = StagehandTool(headless=True)
        
        # Create tools using Stagehand
        self.tools = create_stagehand_tools()
        
        # Create the agent using ReAct framework with custom or default prompt
        prompt = PromptTemplate.from_template(prompt_template or DEFAULT_PLAYWRIGHT_PROMPT)
        self.agent = create_react_agent(self.llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            handle_parsing_errors=True  # More graceful error handling
        )
    
    async def execute_steps(self, test_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute test steps directly using Stagehand tools."""
        steps_text = "\n".join([
            f"Step {i+1}: {self._format_step(step)}"
            for i, step in enumerate(test_steps)
        ])
        
        input_text = (
            "Execute the following test steps using Stagehand. "
            "For each step, use the appropriate Stagehand tool (act, extract, or observe).\n"
            "Remember that Stagehand works best with atomic, specific instructions.\n"
            f"{steps_text}"
        )
        
        try:
            # Start the browser if not already started
            if not self.browser.browser:
                await self.browser.start()
                
            # First, observe the page to understand what's available
            observation_result = None
            
            # Execute steps directly with Stagehand
            results = []
            for i, step in enumerate(test_steps):
                step_result = {"step": i+1, "instruction": self._format_step(step), "success": False}
                
                try:
                    # For each step, first observe the page to get context if needed
                    if i == 0 or step.get("action") == "navigate":
                        # Only observe after navigation or at the beginning
                        observation_result = await self.browser.observe()
                        step_result["observation"] = "Page observed for context"
                    
                    # Execute the step
                    stagehand_result = await self._execute_single_step(step)
                    step_result.update(stagehand_result)
                    step_result["success"] = stagehand_result.get("success", False)
                    
                    # Take a screenshot after each step for debugging
                    screenshot_path = f"step_{i+1}_{step.get('action', 'unknown')}.png"
                    await self.browser.take_screenshot(screenshot_path)
                    step_result["screenshot"] = screenshot_path
                    
                except Exception as e:
                    step_result["error"] = str(e)
                    logger.error(f"Error executing step {i+1}: {str(e)}")
                
                results.append(step_result)
                
                # If a step fails, we might want to continue with the next steps
                # but log the failure
                if not step_result.get("success", False):
                    logger.warning(f"Step {i+1} failed, continuing with next steps")
            
            # Also run through the agent for more complex reasoning
            agent_result = await self.agent_executor.ainvoke({"input": input_text})
            
            return {
                "success": all(result.get("success", False) for result in results), 
                "stagehand_results": results,
                "agent_result": agent_result,
                "observation": observation_result
            }
        except Exception as e:
            logger.error(f"Error executing test steps: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _execute_single_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single test step using the appropriate Stagehand method."""
        action = step.get("action", "unknown").lower()
        
        if action == "navigate":
            url = step.get("url", "")
            return await self.browser.navigate(url)
            
        elif action == "click":
            element = step.get("element", "")
            instruction = f"click on {element}"
            return await self.browser.act(instruction)
            
        elif action == "type" or action == "fill":
            element = step.get("element", "")
            text = step.get("text", "")
            instruction = f"type '{text}' in the {element}"
            return await self.browser.act(instruction)
            
        elif action == "wait":
            seconds = step.get("seconds", 1)
            await asyncio.sleep(seconds)
            return {"success": True, "message": f"Waited for {seconds} seconds"}
            
        elif action == "verify":
            verify_type = step.get("type", "")
            if verify_type == "text_present":
                text = step.get("text", "")
                instruction = f"check if the text '{text}' is present on the page"
                return await self.browser.extract(instruction)
            elif verify_type == "element_visible":
                element = step.get("element", "")
                instruction = f"check if the element '{element}' is visible"
                return await self.browser.extract(instruction)
            else:
                # Generic verification
                return await self.browser.extract(f"verify: {step}")
                
        elif action == "hover":
            element = step.get("element", "")
            instruction = f"hover over {element}"
            return await self.browser.act(instruction)
            
        elif action == "select":
            element = step.get("element", "")
            value = step.get("value", "")
            instruction = f"select '{value}' from the {element} dropdown"
            return await self.browser.act(instruction)
            
        else:
            # For unknown actions, convert to natural language and use act
            instruction = self._format_step(step)
            return await self.browser.act(instruction)
    
    def preview_prompt(self, test_steps: List[Dict[str, Any]]) -> str:
        """Preview the actual prompt that will be sent to the LLM.
        
        Args:
            test_steps: List of test steps to execute
            
        Returns:
            Formatted prompt text
        """
        steps_text = "\n".join([
            f"Step {i+1}: {self._format_step(step)}"
            for i, step in enumerate(test_steps)
        ])
        
        template = (
            "Execute the following test steps using Stagehand. "
            "For each step, use the appropriate Stagehand tool (act, extract, or observe).\n"
            "Remember that Stagehand works best with atomic, specific instructions.\n"
            "{input}"
        )
        
        return template.format(input=steps_text)
    
    @staticmethod
    def _format_step(step: Dict[str, Any]) -> str:
        """Format a test step into a clear natural language instruction for Stagehand."""
        action = step.get("action", "unknown")
        match action:
            case "navigate":
                return f"Navigate to the website '{step.get('url', '')}'"
            case "click":
                element = step.get("element", "")
                # Make the instruction more natural for Stagehand
                if element.startswith("#") or element.startswith(".") or element.startswith("//"):
                    return f"Click on the element with selector '{element}'"
                else:
                    return f"Click on the {element}"
            case "type" | "fill":
                element = step.get("element", "")
                text = step.get("text", "")
                if element.startswith("#") or element.startswith(".") or element.startswith("//"):
                    return f"Type '{text}' in the element with selector '{element}'"
                else:
                    return f"Type '{text}' in the {element}"
            case "wait":
                return f"Wait for {step.get('seconds', 0)} seconds"
            case "verify":
                verify_type = step.get("type", "")
                match verify_type:
                    case "text_present":
                        return f"Check if the text '{step.get('text', '')}' is present on the page"
                    case "element_visible":
                        element = step.get("element", "")
                        if element.startswith("#") or element.startswith(".") or element.startswith("//"):
                            return f"Check if the element with selector '{element}' is visible"
                        else:
                            return f"Check if the {element} is visible"
                    case _:
                        return f"Verify: {step}"
            case "hover":
                element = step.get("element", "")
                if element.startswith("#") or element.startswith(".") or element.startswith("//"):
                    return f"Hover over the element with selector '{element}'"
                else:
                    return f"Hover over the {element}"
            case "select":
                element = step.get("element", "")
                value = step.get("value", "")
                if element.startswith("#") or element.startswith(".") or element.startswith("//"):
                    return f"Select '{value}' from the dropdown with selector '{element}'"
                else:
                    return f"Select '{value}' from the {element} dropdown"
            case _:
                return str(step)
    
    async def cleanup(self):
        """Clean up resources and close the browser."""
        try:
            if self.browser:
                # Take a final screenshot before closing
                try:
                    await self.browser.take_screenshot("final_state.png")
                except Exception as e:
                    logger.warning(f"Failed to take final screenshot: {str(e)}")
                
                # Close the browser
                await self.browser.close()
                logger.info("Browser closed successfully")
            
            return {"success": True, "message": "Resources cleaned up successfully"}
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            return {"success": False, "error": str(e)}

    @classmethod
    def create_specialized_agent(cls, agent_type: str, llm_config: Optional[LLMConfig] = None, headless: bool = True):
        """Create a specialized Stagehand agent for specific testing needs.
        
        Args:
            agent_type: Type of specialized agent ('default', 'accessibility', 'performance', 'visual')
            llm_config: Configuration for the LLM
            headless: Whether to run the browser in headless mode
            
        Returns:
            A specialized PlaywrightCodeGenerator instance with Stagehand
        """
        prompt_template = None
        
        match agent_type.lower():
            case "accessibility":
                prompt_template = ACCESSIBILITY_TESTING_PROMPT
                # For accessibility testing, we might want to use specific tools
                # that check for ARIA attributes, contrast, etc.
            case "performance":
                prompt_template = PERFORMANCE_TESTING_PROMPT
                # For performance testing, we might want to configure Stagehand
                # to collect performance metrics
            case "visual":
                # For visual testing, we might want to configure Stagehand
                # to take more screenshots and compare them
                prompt_template = DEFAULT_PLAYWRIGHT_PROMPT
                headless = False  # Visual testing works better with headed mode
            case "default" | _:
                prompt_template = DEFAULT_PLAYWRIGHT_PROMPT
        
        # Create the agent with the specified configuration        
        agent = cls(llm_config=llm_config, prompt_template=prompt_template)
        
        # Configure the Stagehand tool with the appropriate settings
        agent.browser = StagehandTool(headless=headless)
        
        return agent 