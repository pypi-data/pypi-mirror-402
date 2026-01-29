# rmc-mcp

A Model Context Protocol (MCP) server that wraps prompts with **recursive meta-cognition instructions** for AI code assistants like Claude Code, Cursor, and GitHub Copilot.

## What is Recursive Meta-Cognition?

Recursive meta-cognition is a prompting technique that instructs AI assistants to implement solutions through multiple layers of self-reflection. Instead of generating code in one pass, the AI:

1. **Breaks tasks into layers** - Divides implementation into distinct phases
2. **Self-reflects after each layer** - Evaluates what was done correctly, what edge cases are missing, and what could be improved
3. **Iteratively refines** - Applies improvements before moving to the next layer
4. **Final comprehensive review** - Performs a thorough review after all layers are complete

This approach produces more thoughtful, robust implementations by forcing the AI to pause and critically evaluate its own work.

## Features

- **Single MCP tool**: `wrap_prompt` - wraps any prompt with meta-cognition instructions
- **Configurable layers**: 1-10 layers of recursive self-reflection (default: 3)
- **Cost-effective**: Uses DeepSeek API (significantly cheaper than OpenAI/Anthropic)
- **Works with any AI assistant**: Output can be used with Claude, Cursor, Copilot, ChatGPT, etc.

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- [Claude Code](https://claude.ai/code) CLI
- DeepSeek API key

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/gumruyanzh/rmc-mcp.git
cd rmc-mcp
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Get your DeepSeek API key

1. Go to [DeepSeek Platform](https://platform.deepseek.com/api_keys)
2. Create an account (if you don't have one)
3. Generate a new API key
4. Copy the key for the next step

### 4. Add to Claude Code

```bash
claude mcp add rmc-mcp \
  -s user \
  -e DEEPSEEK_API_KEY="your-api-key-here" \
  -- uv run --directory /path/to/rmc-mcp rmc-mcp
```

Replace `/path/to/rmc-mcp` with the actual path where you cloned the repo.

### 5. Restart Claude Code

Exit and reopen Claude Code for the `wrap_prompt` tool to become available.

## Usage

Once installed, use the `wrap_prompt` tool in Claude Code:

### Basic usage

```
Use wrap_prompt: "Create a REST API for user authentication with JWT tokens"
```

### With more layers for complex tasks

```
Use wrap_prompt with 5 layers: "Build a React dashboard with real-time data visualization, filtering, and export functionality"
```

### With fewer layers for simple tasks

```
Use wrap_prompt with 2 layers: "Add input validation to the user registration form"
```

## Tool Reference

### `wrap_prompt`

Wraps a prompt with recursive meta-cognition instructions.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `prompt` | string | Yes | - | The prompt to wrap with meta-cognition instructions |
| `layers` | integer | No | 3 | Number of meta-cognition layers (1-10) |
| `max_tokens` | integer | No | 2000 | Maximum tokens for the response |

**Returns:** A wrapped meta-prompt ready to use with any AI code assistant.

## Example Output

When you call:
```
Use wrap_prompt: "Create a Python function that validates email addresses"
```

The tool returns a structured meta-prompt like:

```
**META-PROMPT: RECURSIVE META-COGNITION FOR CODE GENERATION**

You are to implement the following technical requirement using a structured,
self-reflective approach. Follow this exact process:

## LAYER BREAKDOWN

### Layer 1: Basic Structure & Core Validation
- Basic function signature and structure
- Core email format validation
- Simple regex or string-based validation

**SELF-REFLECTION AFTER LAYER 1:**
1. What was implemented correctly?
2. What edge cases might be missing?
3. What could be improved before proceeding?

### Layer 2: RFC-Compliant Validation Enhancement
...

### Layer 3: Production-Ready Enhancements
...

## FINAL COMPREHENSIVE REVIEW
...
```

You then use this output with any AI assistant to get a more thoughtful implementation.

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                        Your Prompt                               │
│  "Create a REST API for user authentication"                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     rmc-mcp Server                               │
│  1. Takes your prompt                                            │
│  2. Sends to DeepSeek with meta-cognition template               │
│  3. Returns wrapped prompt with layer instructions               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Wrapped Meta-Prompt                            │
│  - Layer-based implementation plan                               │
│  - Self-reflection questions after each layer                    │
│  - Final review criteria                                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Use with Any AI Assistant                           │
│  Claude Code, Cursor, Copilot, ChatGPT, etc.                     │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
rmc-mcp/
├── pyproject.toml              # Project config + dependencies
├── src/
│   └── rmc_mcp/
│       ├── __init__.py         # Package initialization
│       ├── server.py           # MCP server with wrap_prompt tool
│       └── prompts.py          # Meta-cognition prompt template
├── meta_prompt_wrapper.sh      # Original shell script (reference)
└── README.md
```

## Configuration Options

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DEEPSEEK_API_KEY` | Yes | Your DeepSeek API key |

### MCP Server Scopes

You can install the server at different scopes:

**User scope** (recommended) - Available in all your projects:
```bash
claude mcp add rmc-mcp -s user -e DEEPSEEK_API_KEY="..." -- uv run --directory /path/to/rmc-mcp rmc-mcp
```

**Project scope** - Available only in a specific project:
```bash
claude mcp add rmc-mcp -s project -e DEEPSEEK_API_KEY="..." -- uv run --directory /path/to/rmc-mcp rmc-mcp
```

## Troubleshooting

### "DEEPSEEK_API_KEY not set" error

Make sure you included the `-e DEEPSEEK_API_KEY="your-key"` flag when adding the MCP server:

```bash
claude mcp add rmc-mcp -s user -e DEEPSEEK_API_KEY="your-key" -- uv run --directory /path/to/rmc-mcp rmc-mcp
```

### Tool not appearing in Claude Code

1. Make sure you ran `uv sync` in the project directory
2. Restart Claude Code completely (exit and reopen)
3. Check the MCP server is registered: `claude mcp list`

### Testing the server manually

```bash
# Should start and wait for stdio input (Ctrl+C to exit)
DEEPSEEK_API_KEY="your-key" uv run rmc-mcp
```

### Testing with MCP Inspector

```bash
npx @anthropic-ai/mcp-inspector uv run --directory /path/to/rmc-mcp rmc-mcp
```

## Why DeepSeek?

This tool uses DeepSeek instead of OpenAI or Anthropic APIs because:

1. **Cost-effective**: DeepSeek is significantly cheaper per token
2. **Quality**: DeepSeek-chat produces high-quality prompt transformations
3. **OpenAI-compatible API**: Easy to integrate using the OpenAI Python SDK

You can get a DeepSeek API key at https://platform.deepseek.com/api_keys

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
