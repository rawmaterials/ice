from ice.recipe import recipe
from ice.utils import map_async

from recipes.abstract_qa import Abstract
from recipes.abstract_qa import abstract_qa
from recipes.abstract_qa import DEFAULT_ABSTRACTS
from recipes.combine_abstract_answers import combine_abstract_answers


async def synthesize_compositional(abstracts: list[Abstract], question: str) -> str:
    answers = await map_async(
        abstracts, lambda abstract: abstract_qa(abstract=abstract, question=question)
    )
    answer = await combine_abstract_answers(
        question=question, abstracts=abstracts, answers=answers
    )
    return answer


async def synthesize_compositional_cli() -> str:
    abstracts = DEFAULT_ABSTRACTS
    question = "what is the relationship between income and smoking?"
    answer = await synthesize_compositional(abstracts=abstracts, question=question)
    return answer


recipe.main(synthesize_compositional_cli)
