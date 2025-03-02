"""
Prompt templates for the test platform agents.
"""

from .test_prompts import TEST_EXECUTION_PROMPT
from .code_gen_prompts import CODE_GENERATION_PROMPT, CODE_EXECUTION_PROMPT

__all__ = [
    "TEST_EXECUTION_PROMPT",
    "CODE_GENERATION_PROMPT",
    "CODE_EXECUTION_PROMPT",
] 