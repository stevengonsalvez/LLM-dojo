# Automated Testing Platform (ATP) - Claude Context

## Project Overview
Building an automated testing platform using LangGraph for end-to-end testing with natural language test cases.

## Current Implementation
- Using Python with LangGraph for workflow management
- Browser-Use for browser automation
- Simple text format for test cases
- RAG for storing successful patterns

## Key Components
1. **Test Parser**: Converts natural language to executable steps
2. **LangGraph Agents**: Manages test execution, fixing, and memory
3. **Browser Automation**: Uses Browser-Use for web interactions
4. **Storage**: Local storage for scripts and results

## Test Case Format
Tests are written in plain English with simple commands:
```
navigate to bbc.co.uk
hover over news tab
click sports link
verify text "Sport" is present
```

## Project Structure
```
langraph-testing/
├── src/
│   ├── agents/
│   │   └── test_executor.py      # Executes test steps using LangGraph
│   ├── browser/
│   │   └── browser_wrapper.py    # Wrapper for Browser-Use
│   ├── storage/
│   │   └── rag_store.py          # Storage for successful patterns
│   ├── parser.py                 # Parses natural language test cases
│   └── cli.py                    # CLI interface
├── examples/                     # Example test cases
├── tests/                        # Unit tests
│   └── test_parser.py            # Tests for the parser
├── main.py                       # Entry point
├── requirements.txt              # Project dependencies
├── .env.template                 # Environment variables template
├── Makefile                      # Common commands
└── README.md                     # Project documentation
```

## Current Features
- Natural language test case parsing (navigate, click, hover, wait, verify)
- Browser automation using Browser-Use with LLM translation
- LangGraph workflow for test execution
- RAG-based storage for test patterns and results
- CLI for running and parsing tests

