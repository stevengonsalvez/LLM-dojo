# Automated Testing Platform

An automated testing platform using LangGraph for end-to-end testing with natural language test cases.

## Overview

This project allows you to write test cases in simple natural language and executes them using browser automation. The system leverages LangGraph for workflow management and Browser-Use for web interactions.

## Features

- Simple, natural language test case format
- LangGraph-based workflow for test execution and fixing
- Browser automation using Browser-Use
- Memory of successful patterns with RAG

## Getting Started

### Installation

```bash
# Clone the repository
git clone <repository-url>

# Navigate to the project directory
cd langraph-testing

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.template .env
# Edit .env file with your API keys
```

### Usage

1. Create a test file:

```
# example.test
navigate to bbc.co.uk
hover over news tab
click sports link
verify text "Sport" is present
```

2. Run the test:

```bash
python main.py run --test-file examples/bbc_test.txt --verbose
```

3. Parse a test without running:

```bash
python main.py parse --test-file examples/bbc_test.txt
```

## LangGraph Workflow

### Understanding the Graph

The project uses LangGraph to manage the test execution workflow. The graph consists of the following nodes:

- **parse_test**: Parses the test file into executable steps
- **execute_step**: Executes the current step and updates results
- **finalize**: Finalizes the test execution and cleans up resources

### Visualizing the Graph

To visualize the LangGraph workflow, add the following code to the end of `main.py`:

```python
def visualize_graph():
    from src.agents.test_executor import build_langgraph_workflow
    import os
    
    # Build the workflow
    workflow = build_langgraph_workflow(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    # Export the graph to a file
    workflow.export_to("langgraph_workflow.json")
    
    print("Graph exported to langgraph_workflow.json")
    print("To visualize, visit https://langraph.ai/playground and upload the JSON file")

if __name__ == "__main__":
    # Choose whether to run the CLI or visualize the graph
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "visualize":
        visualize_graph()
    else:
        from src.cli import main
        main()
```

Then run:

```bash
python main.py visualize
```

This will generate a JSON file that you can upload to [LangGraph Playground](https://langraph.ai/playground) for visualization.

### State Flow Through the Graph

LangGraph manages a state object that flows through the nodes in the graph. The state structure is:

```python
class State:
    test_file: str        # Path to the test file
    steps: List[Dict]     # Parsed test steps
    current_step: int     # Index of the current step being executed
    results: List[Dict]   # Results of executed steps
    is_complete: bool     # Whether execution is complete
```

The state flow follows this pattern:

1. **Initial State**: Contains only the test file path
   ```python
   {"test_file": "examples/bbc_test.txt"}
   ```

2. **After parse_test**: State now includes parsed steps
   ```python
   {
     "test_file": "examples/bbc_test.txt",
     "steps": [
       {"action": "navigate", "url": "bbc.co.uk"},
       {"action": "hover", "element": "news tab"},
       ...
     ],
     "current_step": 0,
     "results": []
   }
   ```

3. **After execute_step (first iteration)**: State updated with first result
   ```python
   {
     "test_file": "examples/bbc_test.txt",
     "steps": [...],
     "current_step": 1,
     "results": [{"action": "navigate", "success": true, ...}],
     "is_complete": false
   }
   ```

4. **After finalize**: State marked as complete
   ```python
   {
     "test_file": "examples/bbc_test.txt",
     "steps": [...],
     "current_step": 4,
     "results": [...],
     "is_complete": true
   }
   ```

### Conditional Logic

The graph uses conditional edges to determine flow:

```python
workflow.add_conditional_edges(
    "execute_step",
    lambda state: "finalize" if state["is_complete"] else "execute_step"
)
```

This allows the workflow to either execute another step or finalize based on the current state.

## Project Structure

- `src/`: Source code
  - `agents/`: LangGraph agents for test execution
  - `browser/`: Browser automation utilities
  - `storage/`: Storage mechanisms for test results
  - `parser.py`: Natural language test parser
  - `cli.py`: Command-line interface
- `examples/`: Example test cases
- `tests/`: Unit tests
- `main.py`: Entry point

## Extending the Graph

To add new nodes to the workflow (e.g., a fix agent), modify `src/agents/test_executor.py`:

```python
def build_langgraph_workflow(api_key=None):
    # ... existing code ...
    
    # Add a fix agent node
    async def fix_step(state):
        """Try to fix a failed step."""
        # Implement fix logic here
        return {"fixed_step": True}
    
    workflow.add_node("fix_step", fix_step)
    
    # Update conditional edges
    workflow.add_conditional_edges(
        "execute_step",
        lambda state: (
            "finalize" if state["is_complete"] and state["success"] else
            "fix_step" if not state["success"] else
            "execute_step"
        )
    )
    
    # Connect fix_step back to execute_step
    workflow.add_edge("fix_step", "execute_step")
    
    # ... rest of the function ...
```

This would add a fix agent that attempts to repair failed steps before continuing execution.
