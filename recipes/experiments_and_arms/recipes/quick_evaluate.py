from ice.agents.openai import OpenAIAgent
from ice.recipe import recipe

from recipes.experiments_and_arms.prompts.quick_evaluate import get_grade
from recipes.experiments_and_arms.prompts.quick_evaluate import (
    make_quick_eval_prompt,
)
from recipes.experiments_and_arms.types import ExperimentsArms


async def quick_evaluate(
    gs: ExperimentsArms, generated: ExperimentsArms
) -> tuple[str, str]:
    """Quickly evaluate the generated experiments and arms against the gold standard.

    Args:
        gs (ExperimentsArms): The gold standard.
        generated (ExperimentsArms): The generated answer.

    Returns:
        tuple[str, str]: The evaluation and the letter grade.
    """
    prompt, stop_seq = make_quick_eval_prompt(gs, generated)
    response = await OpenAIAgent().complete(prompt, stop=stop_seq)
    return response, get_grade(response)


recipe.main(quick_evaluate)
