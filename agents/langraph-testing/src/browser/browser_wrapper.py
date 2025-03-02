"""
Wrapper for Browser-Use library for browser automation.
"""
import asyncio
from typing import Dict, Any, Optional
import time
import importlib.util

# Check if browser-use is installed by checking for the module
if importlib.util.find_spec("browser_use") is not None:
    from browser_use import Browser
    BROWSER_USE_AVAILABLE = True
else:
    print("Warning: browser-use not installed. Using mock implementation.")
    Browser = None
    BROWSER_USE_AVAILABLE = False

from ..llm import LLMConfig, LLMProvider

class BrowserUseWrapper:
    """
    Wrapper for Browser-Use library with LLM translation of natural language to browser actions.
    """
    
    def __init__(self, api_key: Optional[str] = None, llm_config: Optional[LLMConfig] = None):
        """
        Initialize the browser wrapper.
        
        Args:
            api_key: Optional API key (legacy, use llm_config instead)
            llm_config: Optional LLM configuration
        """
        # Create LLM provider - either from provided config or from env variables
        if llm_config:
            self.llm_config = llm_config
        elif api_key:
            # Legacy support: create an Anthropic config from api_key
            self.llm_config = LLMConfig(
                provider="anthropic",
                api_key=api_key,
                model="claude-3-sonnet-20240229",
                temperature=0.0
            )
        else:
            # Try to load from environment
            try:
                self.llm_config = LLMConfig.from_env()
            except ValueError:
                self.llm_config = None
                print("Warning: No LLM configuration provided and couldn't load from environment")
        
        # Initialize the LLM provider if we have a config
        self.llm = LLMProvider.create(self.llm_config) if self.llm_config else None
        self.browser = None
        self.is_started = False
    
    async def start(self):
        """Start the browser."""
        if BROWSER_USE_AVAILABLE and not self.is_started:
            try:
                self.browser = Browser()
                await self.browser.start()
                self.is_started = True
                print("Successfully started Browser-Use")
            except Exception as e:
                print(f"Error starting Browser-Use: {str(e)}")
                print("Falling back to mock implementation")
                self.is_started = True
        elif not BROWSER_USE_AVAILABLE:
            print("Mock: Starting browser")
            self.is_started = True
    
    async def stop(self):
        """Stop the browser."""
        if BROWSER_USE_AVAILABLE and self.is_started and self.browser:
            try:
                await self.browser.stop()
            except Exception as e:
                print(f"Error stopping Browser-Use: {str(e)}")
            finally:
                self.is_started = False
        elif not BROWSER_USE_AVAILABLE and self.is_started:
            print("Mock: Stopping browser")
            self.is_started = False
    
    async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a test step.
        
        Args:
            step: Parsed test step
            
        Returns:
            Result of the step execution
        """
        if not self.is_started:
            await self.start()
        
        action = step.get("action", "unknown")
        
        # Handle simple actions directly
        if action == "wait":
            return await self._execute_wait(step)
        
        # Use direct method if available
        method_name = f"_execute_{action}"
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            return await method(step)
        
        # Otherwise, use LLM translation if available
        if self.llm:
            return await self._execute_with_llm(step)
        
        # Fallback to mock implementation
        return {
            "success": False,
            "error": f"Unsupported action: {action}"
        }
    
    async def _execute_navigate(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute navigate action."""
        url = step.get("url", "")
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        
        try:
            if BROWSER_USE_AVAILABLE and self.browser:
                await self.browser.navigate(url)
                print(f"Navigated to {url}")
            else:
                print(f"Mock: Navigating to {url}")
            
            return {
                "success": True,
                "action": "navigate",
                "url": url
            }
        except Exception as e:
            print(f"Error during navigation: {str(e)}")
            return {
                "success": False,
                "action": "navigate",
                "error": str(e)
            }
    
    async def _execute_click(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute click action."""
        element = step.get("element", "")
        
        try:
            if BROWSER_USE_AVAILABLE and self.browser:
                await self.browser.click(element)
                print(f"Clicked on {element}")
            else:
                print(f"Mock: Clicking on {element}")
            
            return {
                "success": True,
                "action": "click",
                "element": element
            }
        except Exception as e:
            print(f"Error during click: {str(e)}")
            return {
                "success": False,
                "action": "click",
                "error": str(e)
            }
    
    async def _execute_hover(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute hover action."""
        element = step.get("element", "")
        
        try:
            if BROWSER_USE_AVAILABLE and self.browser:
                await self.browser.hover(element)
                print(f"Hovered over {element}")
            else:
                print(f"Mock: Hovering over {element}")
            
            return {
                "success": True,
                "action": "hover",
                "element": element
            }
        except Exception as e:
            print(f"Error during hover: {str(e)}")
            return {
                "success": False,
                "action": "hover",
                "error": str(e)
            }
    
    async def _execute_wait(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute wait action."""
        seconds = step.get("seconds", 0)
        
        try:
            if seconds > 0:
                print(f"Waiting for {seconds} seconds")
                time.sleep(seconds)
            
            return {
                "success": True,
                "action": "wait",
                "seconds": seconds
            }
        except Exception as e:
            print(f"Error during wait: {str(e)}")
            return {
                "success": False,
                "action": "wait",
                "error": str(e)
            }
    
    async def _execute_verify(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute verify action."""
        verify_type = step.get("type", "")
        
        try:
            if verify_type == "text_present":
                text = step.get("text", "")
                if BROWSER_USE_AVAILABLE and self.browser:
                    result = await self.browser.evaluate(f"""
                        document.body.innerText.includes("{text}")
                    """)
                    print(f"Verified text '{text}' is present: {result}")
                else:
                    print(f"Mock: Verifying text '{text}' is present")
                    result = True
                
                return {
                    "success": result,
                    "action": "verify",
                    "type": "text_present",
                    "text": text
                }
            elif verify_type == "element_visible":
                element = step.get("element", "")
                if BROWSER_USE_AVAILABLE and self.browser:
                    result = await self.browser.evaluate(f"""
                        !!document.querySelector("{element}")
                    """)
                    print(f"Verified element {element} is visible: {result}")
                else:
                    print(f"Mock: Verifying element {element} is visible")
                    result = True
                
                return {
                    "success": result,
                    "action": "verify",
                    "type": "element_visible",
                    "element": element
                }
            else:
                return {
                    "success": False,
                    "action": "verify",
                    "error": f"Unsupported verification type: {verify_type}"
                }
        except Exception as e:
            print(f"Error during verification: {str(e)}")
            return {
                "success": False,
                "action": "verify",
                "error": str(e)
            }
    
    async def _execute_with_llm(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a step using LLM translation."""
        if not self.llm:
            return {
                "success": False,
                "error": "LLM provider not initialized"
            }
        
        try:
            # Create prompt for the LLM to generate Browser-Use code
            prompt = f"""
            Generate browser-use code for this test step using the Browser class: {step}
            
            Only return the code, no explanation. Use async/await syntax.
            Example:
            await browser.navigate("https://example.com")
            """
            
            # Use the LLM abstraction to generate code
            code = await self.llm.generate(prompt)
            
            # Extract code block if present
            if "```" in code:
                code = code.split("```")[1]
                if code.startswith("javascript") or code.startswith("python"):
                    code = code.split("\n", 1)[1]
                if code.endswith("```"):
                    code = code[:-3]
            
            # Clean up the code
            code = code.strip()
            
            if BROWSER_USE_AVAILABLE and self.browser:
                # Execute the generated code
                local_vars = {"browser": self.browser}
                exec_globals = {"__builtins__": __builtins__}
                
                # Add await if missing
                if not code.startswith("await ") and "await " in code:
                    code = f"await {code}"
                
                # Create an async function and run it
                async_func = f"async def _generated_func():\n    {code.replace('\n', '\n    ')}\n    return True"
                exec(async_func, exec_globals, local_vars)
                result = await local_vars["_generated_func"]()
                print(f"Executed generated code successfully")
                
                return {
                    "success": result,
                    "action": step.get("action", "unknown"),
                    "code": code
                }
            else:
                print(f"Mock: Executing generated code:\n{code}")
                return {
                    "success": True,
                    "action": step.get("action", "unknown"),
                    "code": code
                }
        except Exception as e:
            print(f"Error during LLM execution: {str(e)}")
            return {
                "success": False,
                "action": step.get("action", "unknown"),
                "error": str(e)
            }
