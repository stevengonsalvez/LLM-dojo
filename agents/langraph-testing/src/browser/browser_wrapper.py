"""
Wrapper for Browser-Use library for browser automation.
"""
import asyncio
from typing import Dict, Any, Optional
import time

# Import browser-use when available
try:
    from browser_use import BrowserUse
except ImportError:
    print("Warning: browser-use not installed. Using mock implementation.")
    BrowserUse = None

from anthropic import Anthropic

class BrowserUseWrapper:
    """
    Wrapper for Browser-Use library with LLM translation of natural language to browser actions.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the browser wrapper.
        
        Args:
            api_key: Optional Anthropic API key
        """
        self.client = Anthropic(api_key=api_key) if api_key else None
        self.browser = None
        self.is_started = False
    
    async def start(self):
        """Start the browser."""
        if BrowserUse and not self.is_started:
            self.browser = BrowserUse()
            await self.browser.start()
            self.is_started = True
        elif not BrowserUse:
            print("Mock: Starting browser")
            self.is_started = True
    
    async def stop(self):
        """Stop the browser."""
        if BrowserUse and self.is_started:
            await self.browser.stop()
            self.is_started = False
        elif not BrowserUse and self.is_started:
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
        if self.client:
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
            if BrowserUse:
                await self.browser.navigate(url)
            else:
                print(f"Mock: Navigating to {url}")
            
            return {
                "success": True,
                "action": "navigate",
                "url": url
            }
        except Exception as e:
            return {
                "success": False,
                "action": "navigate",
                "error": str(e)
            }
    
    async def _execute_click(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute click action."""
        element = step.get("element", "")
        
        try:
            if BrowserUse:
                await self.browser.click(element)
            else:
                print(f"Mock: Clicking on {element}")
            
            return {
                "success": True,
                "action": "click",
                "element": element
            }
        except Exception as e:
            return {
                "success": False,
                "action": "click",
                "error": str(e)
            }
    
    async def _execute_hover(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute hover action."""
        element = step.get("element", "")
        
        try:
            if BrowserUse:
                await self.browser.hover(element)
            else:
                print(f"Mock: Hovering over {element}")
            
            return {
                "success": True,
                "action": "hover",
                "element": element
            }
        except Exception as e:
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
                time.sleep(seconds)
            
            return {
                "success": True,
                "action": "wait",
                "seconds": seconds
            }
        except Exception as e:
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
                if BrowserUse:
                    result = await self.browser.evaluate(f"""
                        document.body.innerText.includes("{text}")
                    """)
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
                if BrowserUse:
                    result = await self.browser.evaluate(f"""
                        !!document.querySelector("{element}")
                    """)
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
            return {
                "success": False,
                "action": "verify",
                "error": str(e)
            }
    
    async def _execute_with_llm(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a step using LLM translation."""
        if not self.client:
            return {
                "success": False,
                "error": "Anthropic client not initialized"
            }
        
        try:
            # Create prompt for Claude to generate Browser-Use code
            prompt = f"""
            Generate Browser-Use code for this test step: {step}
            
            Only return the code, no explanation. Use async/await syntax.
            """
            
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20240229",
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            
            code = response.content[0].text
            
            # Extract code block if present
            if "```" in code:
                code = code.split("```")[1]
                if code.startswith("javascript") or code.startswith("python"):
                    code = code.split("\n", 1)[1]
                if code.endswith("```"):
                    code = code[:-3]
            
            # Clean up the code
            code = code.strip()
            
            if BrowserUse:
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
            return {
                "success": False,
                "action": step.get("action", "unknown"),
                "error": str(e)
            }
