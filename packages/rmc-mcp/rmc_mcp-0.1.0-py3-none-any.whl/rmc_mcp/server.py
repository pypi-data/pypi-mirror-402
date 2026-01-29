"""MCP server for recursive meta-cognition prompt wrapping."""

import os

from mcp.server.fastmcp import FastMCP
from openai import OpenAI

from .prompts import get_wrapper_instruction

# Initialize FastMCP server
mcp = FastMCP("rmc-mcp")

# DeepSeek API configuration
DEEPSEEK_API_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"


def get_client() -> OpenAI:
    """Get OpenAI client configured for DeepSeek."""
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError(
            "DEEPSEEK_API_KEY not set. "
            "Get your API key from https://platform.deepseek.com/api_keys then run:\n"
            "claude mcp add rmc-mcp -s user -e DEEPSEEK_API_KEY='your-key-here' "
            "-- uv run --directory /path/to/rmc-mcp rmc-mcp"
        )
    return OpenAI(api_key=api_key, base_url=DEEPSEEK_API_URL)


@mcp.tool()
def wrap_prompt(prompt: str, layers: int = 3, max_tokens: int = 2000) -> str:
    """Wrap a prompt with recursive meta-cognition instructions.

    This tool takes a prompt and wraps it with instructions that tell AI code
    assistants to use a layered, self-reflective approach to implementation.

    Args:
        prompt: The prompt to wrap with meta-cognition instructions
        layers: Number of meta-cognition layers/phases (1-10, default 3)
        max_tokens: Maximum tokens for the response (default 2000)

    Returns:
        The wrapped meta-prompt ready to use with code assistants
    """
    # Validate layers
    if layers < 1:
        layers = 1
    elif layers > 10:
        layers = 10

    # Get the wrapper instruction
    instruction = get_wrapper_instruction(prompt, layers)

    # Call DeepSeek API
    client = get_client()
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[{"role": "user", "content": instruction}],
        max_tokens=max_tokens,
        temperature=0.7,
    )

    return response.choices[0].message.content or ""


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
