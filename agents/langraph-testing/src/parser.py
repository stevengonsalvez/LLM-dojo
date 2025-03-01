"""
Parser for natural language test cases.
"""
from typing import List, Dict, Any
import re

class TestParser:
    """
    Parses natural language test cases into structured steps.
    """
    
    def __init__(self):
        # Define basic command patterns
        self.patterns = {
            r"^navigate to (.+)$": self._parse_navigate,
            r"^click (.+)$": self._parse_click,
            r"^hover over (.+)$": self._parse_hover,
            r"^type (.+) in (.+)$": self._parse_type,
            r"^wait (\d+) seconds?$": self._parse_wait,
            r"^verify (.+)$": self._parse_verify,
        }
    
    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse a test file containing natural language test steps.
        
        Args:
            file_path: Path to the test file
            
        Returns:
            List of parsed test steps
        """
        with open(file_path, "r") as f:
            lines = f.readlines()
        
        # Remove empty lines and strip whitespace
        lines = [line.strip() for line in lines if line.strip()]
        
        return self.parse_lines(lines)
    
    def parse_lines(self, lines: List[str]) -> List[Dict[str, Any]]:
        """
        Parse a list of natural language test steps.
        
        Args:
            lines: List of test step strings
            
        Returns:
            List of parsed test steps
        """
        parsed_steps = []
        
        for line in lines:
            step = self._parse_step(line)
            if step:
                parsed_steps.append(step)
        
        return parsed_steps
    
    def _parse_step(self, step: str) -> Dict[str, Any]:
        """
        Parse a single test step.
        
        Args:
            step: Test step string
            
        Returns:
            Parsed test step as a dictionary
        """
        for pattern, handler in self.patterns.items():
            match = re.match(pattern, step, re.IGNORECASE)
            if match:
                return handler(*match.groups())
        
        # If no pattern matches, return an unknown step
        return {
            "action": "unknown",
            "original": step
        }
    
    def _parse_navigate(self, url: str) -> Dict[str, Any]:
        return {
            "action": "navigate",
            "url": url
        }
    
    def _parse_click(self, element: str) -> Dict[str, Any]:
        return {
            "action": "click",
            "element": element
        }
    
    def _parse_hover(self, element: str) -> Dict[str, Any]:
        return {
            "action": "hover",
            "element": element
        }
    
    def _parse_type(self, text: str, element: str) -> Dict[str, Any]:
        return {
            "action": "type",
            "element": element,
            "text": text
        }
    
    def _parse_wait(self, seconds: str) -> Dict[str, Any]:
        return {
            "action": "wait",
            "seconds": int(seconds)
        }
    
    def _parse_verify(self, condition: str) -> Dict[str, Any]:
        # Handle different verification types
        text_match = re.match(r'text "(.+)" is present', condition)
        if text_match:
            return {
                "action": "verify",
                "type": "text_present",
                "text": text_match.group(1)
            }
        
        element_match = re.match(r'element (.+) is visible', condition)
        if element_match:
            return {
                "action": "verify",
                "type": "element_visible",
                "element": element_match.group(1)
            }
        
        return {
            "action": "verify",
            "condition": condition
        }
