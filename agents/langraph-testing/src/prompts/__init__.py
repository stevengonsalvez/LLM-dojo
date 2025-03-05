"""
Prompt templates for the test platform agents.
"""

from .test_prompts import TEST_EXECUTION_PROMPT
from .code_gen_prompts import (
    DEFAULT_PLAYWRIGHT_PROMPT,
    ACCESSIBILITY_TESTING_PROMPT,
    PERFORMANCE_TESTING_PROMPT
)

__all__ = [
    # Test prompts
    "TEST_EXECUTION_PROMPT",
    
    # Playwright prompts
    "DEFAULT_PLAYWRIGHT_PROMPT",
    "ACCESSIBILITY_TESTING_PROMPT",
    "PERFORMANCE_TESTING_PROMPT",
] 