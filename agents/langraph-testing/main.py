#!/usr/bin/env python
"""
Entry point for the test platform.
"""
import os
import sys

def visualize_graph():
    """
    Visualize the LangGraph workflow.
    Exports the graph to a JSON file that can be uploaded to LangGraph Playground.
    """
    from src.agents.test_executor import build_langgraph_workflow
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Build the workflow
    workflow = build_langgraph_workflow(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    # Export the graph to a file
    output_file = "langgraph_workflow.json"
    workflow.export_to(output_file)
    
    print(f"Graph exported to {output_file}")
    print("To visualize, visit https://langraph.ai/playground and upload the JSON file")

if __name__ == "__main__":
    # Check if we should visualize the graph
    if len(sys.argv) > 1 and sys.argv[1] == "visualize":
        visualize_graph()
    else:
        from src.cli import main
        main()
