#!/usr/bin/env python3
"""
Main entry point for running tests with the platform.
"""
import os
import sys
import asyncio
import argparse
import logging
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv
from .config.graph_config import GraphConfig, ExecutionMode
from .graphs import create_graph
from .llm import LLMConfig

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def run_test(
    test_file: str,
    config: Optional[GraphConfig] = None,
    llm_config: Optional[LLMConfig] = None,
    use_unified: bool = False
) -> Dict[str, Any]:
    """
    Run a test using the configured graph.
    
    Args:
        test_file: Path to the test file
        config: Optional graph configuration
        llm_config: Optional LLM configuration
        use_unified: Whether to use the unified graph
        
    Returns:
        Test execution results
    """
    # Create the appropriate graph based on configuration
    graph = create_graph(config, llm_config, use_unified=use_unified)
    
    # Run the test
    logger.info(f"Running test: {test_file}")
    result = await graph.run(test_file)
    
    return result

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run automated tests")
    parser.add_argument("test_file", help="Path to the test file")
    parser.add_argument(
        "--mode", 
        choices=["direct", "code_gen"], 
        default="direct",
        help="Execution mode (direct or code generation)"
    )
    parser.add_argument(
        "--mcp-url", 
        help="URL for Playwright MCP service (required for code_gen mode)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose output"
    )
    parser.add_argument(
        "--unified",
        action="store_true",
        help="Use the unified graph (composition-based) instead of inheritance-based graphs"
    )
    return parser.parse_args()

async def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    args = parse_args()
    
    # Create graph configuration from arguments
    mode = ExecutionMode.CODE_GEN if args.mode == "code_gen" else ExecutionMode.DIRECT
    
    config = GraphConfig(
        execution_mode=mode,
        playwright_mcp_url=args.mcp_url,
        verbose=args.verbose
    )
    
    # Create LLM configuration from environment
    llm_config = LLMConfig.from_env()
    
    try:
        # Run the test
        result = await run_test(args.test_file, config, llm_config, use_unified=args.unified)
        
        # Print the result summary
        print("\nTest Execution Summary:")
        if "results" in result:
            success_count = sum(1 for r in result["results"] if r.get("success", False))
            total_count = len(result["results"])
            print(f"Steps: {success_count}/{total_count} successful")
        elif "execution_result" in result:
            success = result["execution_result"].get("success", False)
            print(f"Execution {'succeeded' if success else 'failed'}")
            if not success and "error" in result["execution_result"]:
                print(f"Error: {result['execution_result']['error']}")
        
        # Exit with appropriate status code
        if "is_complete" in result and result["is_complete"]:
            if mode == ExecutionMode.DIRECT and "results" in result:
                all_success = all(r.get("success", False) for r in result["results"])
                sys.exit(0 if all_success else 1)
            elif "execution_result" in result:
                sys.exit(0 if result["execution_result"].get("success", False) else 1)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running test: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 