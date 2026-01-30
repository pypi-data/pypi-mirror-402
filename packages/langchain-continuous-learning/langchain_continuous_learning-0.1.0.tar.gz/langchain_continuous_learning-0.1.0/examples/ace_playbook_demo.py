# ruff: noqa: T201
"""ACE Middleware Demo: Watch the Playbook Evolve.

This example demonstrates how the ACE (Agentic Context Engineering) middleware
enables agents to self-improve by maintaining an evolving playbook of strategies
and insights learned from interactions.

The demo shows two modes:
1. **Training mode**: Uses ground truth answers to provide richer feedback to
   the reflector, enabling faster learning.
2. **Inference mode**: Normal usage without ground truth.

Run this script to see the playbook evolve as the agent solves math problems.

Usage:
    export OPENAI_API_KEY="your-key"
    uv run python examples/ace_playbook_demo.py

Note: This demo requires langchain v1 with middleware support. For standalone
usage without the full LangChain v1 agent framework, you can use ACEMiddleware
with your own agent implementation.
"""

import ast
import operator
import re
from collections.abc import Callable
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool

from ace import ACEMiddleware, ACEState, SectionName

# Training data with ground truth
# These are financial word problems where we know the correct answer.
TRAINING_DATA: list[dict[str, str]] = [
    {
        "question": (
            "A software development firm lists its current assets at $1,000,000 "
            "and its current liabilities at $500,000. Find the current ratio."
        ),
        "ground_truth": "2.0",
    },
    {
        "question": (
            "Calculate the ROI for an investor who buys property for $200,000 "
            "and spends an additional $50,000 on renovations, then sells the "
            "property for $300,000."
        ),
        "ground_truth": "0.2",
    },
    {
        "question": (
            "If the return of a portfolio was 8% and the risk-free rate was 2%, "
            "and the standard deviation of the portfolio's excess return was 10%, "
            "calculate the Sharpe Ratio."
        ),
        "ground_truth": "0.6",
    },
    {
        "question": (
            "A pet supplies store had $75,000 in net credit sales and an average "
            "accounts receivable of $15,000 last year. Compute the accounts "
            "receivable turnover."
        ),
        "ground_truth": "5.0",
    },
]

# Inference problems (no ground truth - simulates real usage)
INFERENCE_PROBLEMS: list[str] = [
    "What is 15% of 240?",
    "A shirt costs $45 with 20% off. What's the sale price?",
    "A car travels 180 miles using 6 gallons of gas. "
    "What is its fuel efficiency in miles per gallon?",
]

# Safe math operators for the calculator
_SAFE_OPERATORS: dict[type, Callable[..., float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
}


def _safe_eval(node: ast.AST) -> float:
    """Safely evaluate an AST node containing only math operations."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        msg = f"Unsupported constant type: {type(node.value)}"
        raise ValueError(msg)
    if isinstance(node, ast.BinOp):
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        op = _SAFE_OPERATORS.get(type(node.op))
        if op is None:
            msg = f"Unsupported operator: {type(node.op).__name__}"
            raise ValueError(msg)
        return float(op(left, right))
    if isinstance(node, ast.UnaryOp):
        operand = _safe_eval(node.operand)
        op = _SAFE_OPERATORS.get(type(node.op))
        if op is None:
            msg = f"Unsupported unary operator: {type(node.op).__name__}"
            raise ValueError(msg)
        return float(op(operand))
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    msg = f"Unsupported expression type: {type(node).__name__}"
    raise ValueError(msg)


@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression using Python syntax.

    Args:
        expression: A valid Python math expression
            (e.g., "15 * 0.20" or "1000 * 1.05 ** 3").

    Returns:
        The result of the calculation as a string.
    """
    try:
        tree = ast.parse(expression, mode="eval")
        result = _safe_eval(tree)
        return str(result)
    except Exception as e:
        return f"Error: {e}"


def _print_playbook_state(
    full_state: dict[str, Any],
    previous_playbook_content: str,
    *,
    curator_ran: bool,
) -> str:
    """Print playbook state and return current content for next iteration."""
    playbook_data = full_state.get("ace_playbook")
    if not playbook_data:
        return previous_playbook_content

    content = playbook_data.get("content", "")

    # Detect new insights by comparing bullet IDs
    if curator_ran:
        prev_ids = set(re.findall(r"\[[a-z]{3}-\d{5}\]", previous_playbook_content))
        curr_ids = set(re.findall(r"\[[a-z]{3}-\d{5}\]", content))
        new_ids = curr_ids - prev_ids

        if new_ids:
            print("\n🆕 New insights added:")
            for line in content.split("\n"):
                for new_id in new_ids:
                    if new_id in line:
                        print(f"  + {line.strip()}")
                        break

    print("\n📖 Current Playbook:")
    print("─" * 40)
    for line in content.split("\n"):
        if line.strip():
            print(f"  {line}")
    print("─" * 40)

    # Show the last reflection
    last_reflection = full_state.get("ace_last_reflection", "")
    if last_reflection and last_reflection.strip():
        print("\n💡 Reflection:")
        print("─" * 40)
        for line in last_reflection.split("\n"):
            if line.strip():
                print(f"  {line}")
        print("─" * 40)

    return content


def simulate_agent_response(question: str, ground_truth: str | None = None) -> dict[str, Any]:
    """Simulate an agent response for demonstration purposes.

    In a real LangChain v1 setup, this would be replaced with:
        agent.invoke({"messages": [HumanMessage(content=question)]})

    Args:
        question: The user's question.
        ground_truth: Optional ground truth for training mode.

    Returns:
        Simulated agent state with messages.
    """
    # Simulate a simple response (in practice, this would be the actual agent)
    state: ACEState = {
        "messages": [
            HumanMessage(content=question),
            AIMessage(
                content=(
                    "Let me solve this step by step.\n\n"
                    f"**ANSWER**: {ground_truth or 'computed value'}\n\n"
                    "<!-- bullet_ids: [] -->"
                )
            ),
        ],
    }
    if ground_truth:
        state["ground_truth"] = ground_truth
    return state


def main() -> None:
    """Run the ACE playbook evolution demo."""
    print("=" * 60)
    print("ACE Middleware Demo: Playbook Structure Preview")
    print("=" * 60)
    print()
    print("This demo shows the ACE middleware components.")
    print("For full agent integration, use with LangChain v1's create_agent.")
    print()

    # Create ACE middleware
    ace = ACEMiddleware(
        reflector_model="gpt-4o-mini",  # Will be initialized when first used
        curator_model="gpt-4o-mini",
        curator_frequency=2,
        initial_playbook=f"""## {SectionName.STRATEGIES_AND_INSIGHTS}
[str-00001] helpful=0 harmful=0 :: Break word problems into clear steps before calculating

## {SectionName.COMMON_MISTAKES_TO_AVOID}
[mis-00001] helpful=0 harmful=0 :: Don't forget to include units in the final answer
""",
    )

    print("ACE Middleware Configuration:")
    print(f"  - Reflector model: {ace._reflector_model_spec}")
    print(f"  - Curator model: {ace._curator_model_spec}")
    print(f"  - Curator frequency: {ace.curator_frequency}")
    print(f"  - Playbook token budget: {ace.playbook_token_budget}")
    print()

    print("Initial Playbook:")
    print("─" * 40)
    for line in ace.initial_playbook.split("\n"):
        if line.strip():
            print(f"  {line}")
    print("─" * 40)
    print()

    print("Training Data Examples:")
    for i, item in enumerate(TRAINING_DATA[:2], 1):
        print(f"  {i}. Q: {item['question'][:60]}...")
        print(f"     A: {item['ground_truth']}")
    print()

    print("Inference Problems:")
    for i, problem in enumerate(INFERENCE_PROBLEMS[:2], 1):
        print(f"  {i}. {problem}")
    print()

    print("=" * 60)
    print("Full Integration Example")
    print("=" * 60)
    print()
    print("To use ACE with a LangChain v1 agent:")
    print()
    print("```python")
    print("from langchain.agents import create_agent")
    print("from ace import ACEMiddleware")
    print()
    print("ace = ACEMiddleware(")
    print('    reflector_model="gpt-4o-mini",')
    print('    curator_model="gpt-4o-mini",')
    print(")")
    print()
    print("agent = create_agent(")
    print('    model="gpt-4o",')
    print("    tools=[calculator],")
    print("    middleware=[ace],")
    print(")")
    print()
    print("result = agent.invoke({")
    print('    "messages": [HumanMessage(content="What is 15% of 240?")]')
    print("})")
    print("```")
    print()


if __name__ == "__main__":
    main()
