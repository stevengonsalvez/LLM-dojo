"""
Parser module for test files.
"""
from typing import List, Dict, Any
import os
import re

class TestStepParser:
    """
    Parser for test files to convert natural language to structured steps.
    """
    
    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse a test file into structured steps.
        
        Args:
            file_path: Path to the test file
            
        Returns:
            List of parsed test steps
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Test file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Parse the steps from the file content
        steps = self._parse_steps(content)
        return steps
    
    def _parse_steps(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse test steps from content.
        
        Args:
            content: Test file content
            
        Returns:
            List of parsed test steps
        """
        # Split the content by lines and process each step
        lines = content.strip().split('\n')
        steps = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Remove step numbers if present
            line = re.sub(r'^\d+\.?\s*', '', line)
            
            # Parse the step into a structured format
            step = self._parse_step(line)
            if step:
                steps.append(step)
        
        return steps
    
    def _parse_step(self, step_text: str) -> Dict[str, Any]:
        """
        Parse a single step into a structured format.
        
        Args:
            step_text: Text of the step
            
        Returns:
            Structured step object
        """
        step_text = step_text.strip().lower()
        
        if "navigate" in step_text or "go to" in step_text:
            # Extract URL from quotes if present
            url_match = re.search(r'"([^"]+)"', step_text)
            if url_match:
                url = url_match.group(1)
            else:
                # Try to extract URL without quotes
                url_match = re.search(r'(?:navigate|go)\s+to\s+(.+?)(?:\s|$)', step_text)
                url = url_match.group(1) if url_match else ""
            
            return {"action": "navigate", "url": url}
            
        elif "click" in step_text:
            # Extract element from quotes if present
            element_match = re.search(r'"([^"]+)"', step_text)
            if element_match:
                element = element_match.group(1)
            else:
                # Try to extract element without quotes
                element_match = re.search(r'click\s+(?:on\s+)?(.+?)(?:\s|$)', step_text)
                element = element_match.group(1) if element_match else ""
            
            return {"action": "click", "element": element}
            
        elif "hover" in step_text:
            # Extract element from quotes if present
            element_match = re.search(r'"([^"]+)"', step_text)
            if element_match:
                element = element_match.group(1)
            else:
                # Try to extract element without quotes
                element_match = re.search(r'hover\s+(?:over\s+)?(.+?)(?:\s|$)', step_text)
                element = element_match.group(1) if element_match else ""
            
            return {"action": "hover", "element": element}
            
        elif "wait" in step_text:
            # Extract seconds if present
            seconds_match = re.search(r'(\d+)\s*seconds', step_text)
            seconds = int(seconds_match.group(1)) if seconds_match else 1
            
            return {"action": "wait", "seconds": seconds}
            
        elif "verify" in step_text or "check" in step_text:
            if "text" in step_text and ("present" in step_text or "exists" in step_text or "contains" in step_text):
                # Extract text from quotes if present
                text_match = re.search(r'"([^"]+)"', step_text)
                text = text_match.group(1) if text_match else ""
                
                return {"action": "verify", "type": "text_present", "text": text}
                
            elif ("element" in step_text or "button" in step_text or "link" in step_text) and ("visible" in step_text or "present" in step_text or "exists" in step_text):
                # Extract element from quotes if present
                element_match = re.search(r'"([^"]+)"', step_text)
                element = element_match.group(1) if element_match else ""
                
                return {"action": "verify", "type": "element_visible", "element": element}
        
        # If we can't parse it, return the raw step
        return {"action": "raw", "text": step_text} 