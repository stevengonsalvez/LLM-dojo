"""
Command-line interface for the test platform.
"""
import os
import sys
import argparse
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

from .parser import TestParser
from .agents.test_executor import TestExecutorAgent, build_langgraph_workflow
from .storage.rag_store import RagStore

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test-platform")

class CLI:
    """Command-line interface for the test platform."""
    
    def __init__(self):
        self.parser = argparse.ArgumentParser(description="Test Platform CLI")
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.setup_parser()
    
    def setup_parser(self):
        """Set up the argument parser."""
        subparsers = self.parser.add_subparsers(dest="command", help="Command to run")
        
        # Run command
        run_parser = subparsers.add_parser("run", help="Run a test file")
        run_parser.add_argument("--test-file", "-t", required=True, help="Path to the test file")
        run_parser.add_argument("--output", "-o", help="Path to the output file")
        run_parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
        
        # Parse command
        parse_parser = subparsers.add_parser("parse", help="Parse a test file")
        parse_parser.add_argument("--test-file", "-t", required=True, help="Path to the test file")
        parse_parser.add_argument("--output", "-o", help="Path to the output file")
    
    def run(self):
        """Run the CLI."""
        args = self.parser.parse_args()
        
        if args.command == "run":
            asyncio.run(self.run_test(args))
        elif args.command == "parse":
            self.parse_test(args)
        else:
            self.parser.print_help()
    
    async def run_test(self, args):
        """Run a test file."""
        test_file = args.test_file
        if not os.path.exists(test_file):
            logger.error(f"Test file not found: {test_file}")
            sys.exit(1)
        
        # Create executor
        executor = TestExecutorAgent(api_key=self.api_key)
        
        # Run the test
        logger.info(f"Running test file: {test_file}")
        results = await executor.execute_test(test_file)
        
        # Display results
        success_count = sum(1 for r in results if r.get("success", False))
        logger.info(f"Test completed: {success_count}/{len(results)} steps passed")
        
        if args.verbose:
            for i, result in enumerate(results):
                status = "✅" if result.get("success", False) else "❌"
                logger.info(f"Step {i+1}: {status} {result.get('action', 'unknown')}")
                if not result.get("success", False):
                    logger.error(f"  Error: {result.get('error', 'unknown error')}")
        
        # Save output
        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to: {args.output}")
        
        # Store results in RAG
        rag_store = RagStore()
        parser = TestParser()
        steps = parser.parse_file(test_file)
        
        for step, result in zip(steps, results):
            rag_store.store_step_result(step, result)
        
        # Return success status
        return all(r.get("success", False) for r in results)
    
    def parse_test(self, args):
        """Parse a test file."""
        test_file = args.test_file
        if not os.path.exists(test_file):
            logger.error(f"Test file not found: {test_file}")
            sys.exit(1)
        
        # Parse the test file
        parser = TestParser()
        steps = parser.parse_file(test_file)
        
        # Display steps
        logger.info(f"Parsed {len(steps)} steps from {test_file}")
        for i, step in enumerate(steps):
            logger.info(f"Step {i+1}: {step}")
        
        # Save output
        if args.output:
            with open(args.output, "w") as f:
                json.dump(steps, f, indent=2)
            logger.info(f"Parsed steps saved to: {args.output}")
        
        return steps


def main():
    """Main entry point."""
    cli = CLI()
    cli.run()


if __name__ == "__main__":
    main()
