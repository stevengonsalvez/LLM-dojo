#!/usr/bin/env python3
"""
Main entry point for the test platform.
"""
import sys
import asyncio
import json
import os
import argparse

from src.run import main as run_main
from src.graphs import create_graph
from src.config.graph_config import GraphConfig, ExecutionMode
from src.llm import LLMConfig
from dotenv import load_dotenv
import networkx as nx


def visualize_graph():
    """
    Visualize the graph structure using LangGraph's built-in visualization.
    """
    print("Visualizing graph structure...")
    
    # Load environment variables
    load_dotenv()
    
    # Create LLM configuration from environment
    llm_config = LLMConfig.from_env()
    
    # Create graphs for visualization
    graphs = {
        "direct": create_graph(
            GraphConfig(execution_mode=ExecutionMode.DIRECT),
            llm_config
        ),
        "code_gen": create_graph(
            GraphConfig(execution_mode=ExecutionMode.CODE_GEN),
            llm_config
        ),
        "unified": create_graph(
            GraphConfig(),
            llm_config,
            use_unified=True
        )
    }
    
    # Create output directory if it doesn't exist
    output_dir = "graph_visualizations"
    os.makedirs(output_dir, exist_ok=True)
    
    # Print graph structure for each graph using LangGraph's built-in visualization
    for name, graph_instance in graphs.items():
        print(f"\n{name.upper()} GRAPH:")
        
        # Compile the graph first
        compiled_graph = graph_instance.build_graph().compile()
        
        # Use LangGraph's built-in visualization
        # This will generate a proper mermaid diagram with all nodes and edges
        mermaid_str = compiled_graph.get_graph().draw_mermaid()
        
        # Print the mermaid diagram
        print(mermaid_str)
        
        # Save the mermaid diagram to a file
        output_file = os.path.join(output_dir, f"{name}_graph.mmd")
        with open(output_file, "w") as f:
            f.write(mermaid_str)
        
        print(f"Saved {name} graph to {output_file}")
        
        # Export to JSON for LangGraph Studio
        json_output_file = os.path.join(output_dir, f"{name}_graph.json")
        try:
            # Export the graph to JSON
            graph_json = compiled_graph.get_graph().to_json()
            # Convert the dictionary to a JSON string
            json_str = json.dumps(graph_json, indent=2)
            with open(json_output_file, "w") as f:
                f.write(json_str)
            print(f"Exported {name} graph to {json_output_file} for LangGraph Studio")
        except Exception as e:
            print(f"Error exporting {name} graph to JSON: {str(e)}")
    
    # Create a specific langgraph.json file for LangGraph Studio
    # Include all three graphs for a complete view
    try:
        # Compile all graphs
        compiled_graphs = {}
        for name, graph_instance in graphs.items():
            compiled_graphs[name] = graph_instance.build_graph().compile()
        
        # Create the proper format for LangGraph Studio with all graphs
        # LangGraph Studio expects a 'dependencies' list, not a 'graphs' dictionary
        langgraph_config = {
            "dependencies": [
                {
                    "id": "direct_graph",
                    "type": "graph",
                    "data": compiled_graphs["direct"].get_graph().to_json()
                },
                {
                    "id": "code_gen_graph",
                    "type": "graph",
                    "data": compiled_graphs["code_gen"].get_graph().to_json()
                },
                {
                    "id": "unified_graph",
                    "type": "graph",
                    "data": compiled_graphs["unified"].get_graph().to_json()
                }
            ]
        }
        
        json_str = json.dumps(langgraph_config, indent=2)
        
        # Save to the root directory as langgraph.json
        with open("langgraph.json", "w") as f:
            f.write(json_str)
        print("\nCreated langgraph.json with all graphs in the root directory for LangGraph Studio")
    except Exception as e:
        print(f"\nError creating langgraph.json: {str(e)}")
        
    print(f"\nAll graph visualizations saved to {output_dir}/")
    print("You can view the Mermaid files with any Mermaid viewer or at https://mermaid.live")
    print("You can import the JSON files into LangGraph Studio for interactive visualization")


if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(description="Test platform main entry point")
    parser.add_argument("command", nargs="?", default="run", 
                        choices=["run", "visualize"],
                        help="Command to execute (run or visualize)")
    
    args, remaining = parser.parse_known_args()
    
    if args.command == "visualize":
        visualize_graph()
    else:
        # For the "run" command, pass remaining args to the run module
        sys.argv = [sys.argv[0]] + remaining
        asyncio.run(run_main())
        sys.exit(0)
