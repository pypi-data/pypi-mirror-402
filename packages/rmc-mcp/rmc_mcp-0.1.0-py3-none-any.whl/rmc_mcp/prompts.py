"""Meta-cognition prompt templates."""


def get_wrapper_instruction(prompt: str, layers: int) -> str:
    """Generate the meta-cognition wrapper instruction for the LLM.

    Args:
        prompt: The user's original prompt to wrap
        layers: Number of meta-cognition layers (1-10)

    Returns:
        The instruction to send to the LLM to generate the wrapped prompt
    """
    return f'''You are creating a meta-prompt for AI code assistants (Claude Code, Cursor, Copilot).

The user has this refined technical prompt:
"""
{prompt}
"""

Your task: Wrap this prompt with recursive meta-cognition instructions that tell the code assistant to:

1. **Layer-based implementation**: Break the task into {layers} distinct layers/phases
2. **Self-reflection after each layer**: After completing each layer, pause and evaluate:
   - What was implemented correctly?
   - What edge cases might be missing?
   - What could be improved before proceeding?
3. **Iterative refinement**: Apply improvements before moving to the next layer
4. **Final review**: After all layers, do a comprehensive self-review

Structure the output as a complete prompt that:
- Starts with clear instructions about the recursive meta-cognition approach
- Includes the original technical requirements
- Specifies the layer breakdown
- Defines what self-reflection questions to ask at each layer
- Ends with final validation criteria

Output ONLY the wrapped meta-prompt. No explanations outside the prompt itself. The output should be ready to paste directly into a code assistant.'''
