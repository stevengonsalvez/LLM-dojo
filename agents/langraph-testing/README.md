# Test Automation Platform

A flexible test automation platform that supports multiple execution paths for running browser-based tests.

## Features

- **Multiple Execution Modes**: 
  - Direct execution using Browser-Use
  - Code generation using Playwright MCP

- **Flexible Configuration**:
  - Configure via environment variables
  - Specify execution mode, LLM provider, and other settings

- **Modular Architecture**:
  - Separate graph implementations
  - Pluggable agent components
  - Reusable prompts

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Copy the `.env.template` file to `.env` and configure your settings:
   ```
   cp .env.template .env
   ```

## Configuration

### LLM Configuration

Configure the LLM provider in the `.env` file:

```
LLM_PROVIDER=anthropic  # Options: anthropic, openai, azure
LLM_MODEL=claude-3-sonnet-20240229
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=4096

# Add your API keys
ANTHROPIC_API_KEY=your_api_key_here
```

### Graph Configuration

Configure the execution mode and other settings:

```
EXECUTION_MODE=DIRECT  # Options: DIRECT, CODE_GEN
PLAYWRIGHT_MCP_URL=http://localhost:3000  # Required for CODE_GEN mode
ENABLE_RAG=false
VERBOSE=false
MAX_RETRIES=3
```

## Usage

### Running Tests

Run a test file using the command line:

```bash
python -m src.run tests/example_test.txt
```

Or using the main entry point:

```bash
python main.py tests/example_test.txt
```

### Visualizing Graph Structure

You can visualize the graph structure using the `visualize` command:

```bash
python main.py visualize
```

This will generate a JSON file containing the graph structure for both execution modes (direct and code generation). It also prints a text representation of the nodes and edges.

For a graphical visualization, you can use the generated JSON file with visualization tools like Graphviz, NetworkX with matplotlib, or online tools like Gephi.

Optional arguments:
- `--output`: Specify the output file path (default: `graph_visualization.json`)

```bash
python main.py visualize --output my_graph.json
```

### Command Line Options

- `--mode`: Execution mode (`direct` or `code_gen`)
- `--mcp-url`: URL for Playwright MCP service (required for code_gen mode)
- `--verbose`: Enable verbose output

Example:

```bash
python -m src.run tests/example_test.txt --mode code_gen --mcp-url http://localhost:3000
```

### Creating Test Files

Test files are text files containing step-by-step instructions. For example:

```
1. Navigate to "https://example.com"
2. Click on the button with text "Login"
3. Fill in the input with name "username" with "testuser"
4. Fill in the input with name "password" with "password123"
5. Click on the button with text "Submit"
6. Verify that text "Welcome, testuser" is present
```

## Project Structure

```
├── src/
│   ├── agents/
│   │   ├── code_generator.py  # Playwright code generator
│   │   └── test_executor.py   # Direct test executor
│   ├── config/
│   │   ├── graph_config.py    # Graph configuration
│   │   └── __init__.py        # Config module init
│   ├── graphs/
│   │   ├── base_graph.py      # Base graph class
│   │   ├── code_gen_graph.py  # Code generation graph
│   │   ├── factory.py         # Graph factory
│   │   ├── test_graph.py      # Direct test execution graph
│   │   └── __init__.py        # Graphs module init
│   ├── llm/
│   │   └── ...                # LLM providers
│   ├── prompts/
│   │   ├── code_gen_prompts.py # Code generation prompts
│   │   ├── test_prompts.py     # Test execution prompts
│   │   └── __init__.py         # Prompts module init
│   └── run.py                  # Main entry point
├── tests/
│   └── ...                     # Test files
├── .env.template               # Environment variables template
└── requirements.txt            # Dependencies
```

## Extending the Platform

### Adding a New Execution Mode

1. Create a new graph implementation in `src/graphs/`
2. Add the new mode to the `ExecutionMode` enum in `src/config/graph_config.py`
3. Update the factory function in `src/graphs/factory.py`

### Adding New Agent Capabilities

1. Create or modify agent implementation in `src/agents/`
2. Add new prompts in `src/prompts/` if needed
3. Integrate with the appropriate graph implementation

## License

MIT
