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


def visualize_graph(output_file="graph_visualization.json"):
    """
    Visualize the graph structure and save it to a JSON file.
    
    Args:
        output_file: Output file path for the visualization data
    """
    print("Visualizing graph structure...")
    
    # Load environment variables
    load_dotenv()
    
    # Create graph configuration from environment
    config = GraphConfig.from_env()
    
    # Create LLM configuration from environment
    llm_config = LLMConfig.from_env()
    
    # Create both types of graphs for visualization
    graphs = {
        "direct": create_graph(
            GraphConfig(execution_mode=ExecutionMode.DIRECT),
            llm_config
        ),
        "code_gen": create_graph(
            GraphConfig(execution_mode=ExecutionMode.CODE_GEN),
            llm_config
        )
    }
    
    # Create a dictionary to store the visualization data
    visualization_data = {}
    
    for name, graph_instance in graphs.items():
        # Build the graph
        workflow = graph_instance.get_graph()
        
        # Extract nodes and edges from the graph
        graph_data = {
            "nodes": [],
            "edges": []
        }
        
        # Get nodes from the graph
        for node_name in workflow.nodes:
            graph_data["nodes"].append({
                "id": node_name,
                "label": node_name
            })
        
        # Add END node if not already included
        end_node_names = ["END", "__end__"]
        if not any(node["id"] in end_node_names for node in graph_data["nodes"]):
            graph_data["nodes"].append({
                "id": "END",
                "label": "END"
            })
        
        # Get edge information through introspection
        # This is a simplified approach and might need adjustments based on langgraph version
        
        # Try to get _checkpointed_edges which holds edge information in some versions
        if hasattr(workflow, "_checkpointed_edges"):
            edges = workflow._checkpointed_edges
            for edge in edges:
                source, target = edge[0], edge[1]
                graph_data["edges"].append({
                    "source": source,
                    "target": target
                })
        
        # Try to get edge information from the graph definition
        def extract_node_connections(workflow):
            connections = []
            
            # Regular edges
            if hasattr(workflow, "_graph"):
                for node_name in workflow.nodes:
                    if node_name == "END" or node_name == "__end__":
                        continue
                    
                    # Check for direct node connections
                    node_def = workflow._graph.get(node_name, {})
                    if isinstance(node_def, dict) and "next" in node_def:
                        next_nodes = node_def["next"]
                        if isinstance(next_nodes, list):
                            for next_node in next_nodes:
                                connections.append((node_name, next_node))
                        elif isinstance(next_nodes, str):
                            connections.append((node_name, next_nodes))
            
            # Try to extract conditional edges
            if hasattr(workflow, "_conditional_edges"):
                for source, edge_info in workflow._conditional_edges.items():
                    for target in edge_info.get("targets", []):
                        connections.append((source, target))
            
            return connections
        
        edges = extract_node_connections(workflow)
        for source, target in edges:
            graph_data["edges"].append({
                "source": source,
                "target": target
            })
        
        # For StateGraph: try to extract entry point connection
        if hasattr(workflow, "entry_point"):
            entry_point = workflow.entry_point
            if entry_point:
                graph_data["nodes"].insert(0, {
                    "id": "START",
                    "label": "START" 
                })
                graph_data["edges"].insert(0, {
                    "source": "START",
                    "target": entry_point
                })
        
        # Add to visualization data
        visualization_data[name] = graph_data
    
    # Save to file
    with open(output_file, "w") as f:
        json.dump(visualization_data, f, indent=2)
    
    print(f"Graph visualization data saved to {output_file}")
    
    # Print text representation
    for name, graph_data in visualization_data.items():
        print(f"\n{name.upper()} GRAPH:")
        print("Nodes:")
        for node in graph_data["nodes"]:
            print(f"- {node['id']}")
        
        print("\nEdges:")
        for edge in graph_data["edges"]:
            print(f"- {edge['source']} → {edge['target']}")
    
    # Create a fallback simple representation if no edges were found
    for name, graph_instance in graphs.items():
        if not visualization_data[name]["edges"]:
            print(f"\nFallback representation for {name.upper()} GRAPH:")
            if name == "direct":
                print("Nodes: parse_test → execute_step → finalize → END")
            else:
                print("Nodes: parse_test → generate_code → execute_code → END")
    
    print("\nTo visualize these graphs graphically, you can use network visualization tools")
    print("or libraries like Graphviz, NetworkX with matplotlib, or online tools like Gephi.")


if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(description="Test platform main entry point")
    parser.add_argument("command", nargs="?", default="run", 
                        choices=["run", "visualize"],
                        help="Command to execute (run or visualize)")
    parser.add_argument("--output", default="graph_visualization.json", 
                        help="Output file for graph visualization (used with visualize command)")
    
    args, remaining = parser.parse_known_args()
    
    if args.command == "visualize":
        visualize_graph(args.output)
    else:
        # For the "run" command, pass remaining args to the run module
        sys.argv = [sys.argv[0]] + remaining
        asyncio.run(run_main())
        sys.exit(0)
