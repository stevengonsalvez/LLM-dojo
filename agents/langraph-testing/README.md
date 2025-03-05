# LangGraph Testing with Stagehand

This project implements a testing framework using LangGraph and Stagehand for browser automation.

## Features

- **Stagehand Integration**: Uses Stagehand's AI-powered browser automation capabilities
- **LangGraph Workflow**: Implements a flexible graph-based workflow for test execution
- **Natural Language Testing**: Write tests in natural language and have them executed automatically

## Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Install Playwright browsers:

```bash
playwright install
```

## Usage

### Running Tests

```bash
python main.py run --test-file tests/example.test
```

### Visualizing the Graph

```bash
python main.py visualize
```

## Stagehand Features

Stagehand provides three main APIs for browser automation:

1. **act()**: Perform actions on the page (click, type, etc.)
2. **extract()**: Extract data from the page
3. **observe()**: Get suggestions for possible actions on the current page

Example:

```python
from src.tools.stagehand_tool import StagehandTool

async def run_example():
    tool = StagehandTool()
    await tool.start()
    
    # Navigate to a website
    await tool.navigate("https://example.com")
    
    # Perform an action using natural language
    await tool.act("click the login button")
    
    # Extract data using natural language
    data = await tool.extract("get the title of the page")
    print(data)
    
    # Get suggestions for possible actions
    suggestions = await tool.observe()
    print(suggestions)
    
    await tool.close()
```

## Architecture

The project uses a unified graph architecture with multiple execution paths:

1. **Direct Execution**: Executes test steps directly using Stagehand
2. **Code Generation**: Generates and executes Playwright code for test steps
3. **Unified Approach**: Combines both approaches for maximum flexibility

## License

MIT
