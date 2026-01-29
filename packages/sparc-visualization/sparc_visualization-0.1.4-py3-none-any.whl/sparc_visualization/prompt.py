from typing import Dict

from sparc_visualization.prompts.prompts import get_prompt


def generate_prompt(
    puzzle: Dict,
    plot_type: str = "original",
    prompt_type: str = "prompt_engineering",
) -> str:
    """Generate a model prompt for a given board.

    Parameters
    ----------
    prompt_type:
        - "default_tr": visual prompt from the SPaRC paper (with textual coordinates)
        - "default_no_tr": visual prompt from the SPaRC paper (however with textual coordinates removed)
        - "prompt_engineering": improved vision-only prompt with prompt engineering (no textual coordinates)
    plot_type:
        Passed through to the underlying prompt implementation.
    puzzle:
        The puzzle data of a single SPaRC puzzle.
    """
    return get_prompt(prompt_type, plot_type, puzzle)