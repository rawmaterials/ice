from collections.abc import Callable
from collections.abc import Sequence
from functools import partial

from ice.apis.openai import TooLongRequestError
from ice.formatter.transform.value import numbered_list
from ice.paper import Paper
from ice.recipe import recipe
from ice.recipes.meta.eval_paper_qa.quick_list import quick_list
from ice.recipes.meta.eval_paper_qa.types import PaperQaAnswer
from ice.recipes.meta.eval_paper_qa.types import PaperQaGoldStandard
from ice.recipes.meta.eval_paper_qa.types import PaperQaMethod
from ice.recipes.meta.eval_paper_qa.utils import convert_demonstration_example
from ice.recipes.meta.eval_paper_qa.utils import identify_gs_str
from ice.recipes.primer.paper_qa import answer_for_paper
from ice.recipes.primer.qa import answer
from ice.recipes.program_search.nodes.answer.answer import demonstration_answer
from ice.recipes.program_search.nodes.answer.answer import (
    demonstration_answer_with_reasoning,
)
from ice.recipes.program_search.nodes.answer.types import Demonstration
from ice.recipes.program_search.nodes.select.select import as_bool
from ice.utils import map_async


async def _cheating_qa_baseline(
    paper: Paper,
    question: str,
    gold_support: Sequence[str] | None,
    enumerate_answer: bool,
):
    """Baseline that uses gold standard support, without searching the paper.
    (hence "cheating")

    Args:
        paper (Paper): _description_
        question (str): _description_
        gold_support (Sequence[str] | None): _description_
        enumerate_answer (bool, optional): _description_. Defaults to False.

    Raises:
        ValueError: _description_

    Returns:
        _type_: _description_
    """
    relevant_str = "\n\n".join(gs for gs in gold_support) if gold_support else ""
    if not relevant_str:
        raise ValueError("Method requires gold support")
    response: str | Sequence[str] = await answer(
        context=relevant_str, question=question
    )
    if enumerate_answer:
        response = await quick_list(question, str(response))
    assert gold_support
    return PaperQaAnswer(
        answer=response,
        support_candidates=gold_support,
        support_labels=[True for _ in gold_support],
    )


cheating_qa_baseline_str_answer: PaperQaMethod[str] = partial(
    _cheating_qa_baseline, enumerate_answer=False
)
cheating_qa_baseline_list_answer: PaperQaMethod[Sequence[str]] = partial(
    _cheating_qa_baseline, enumerate_answer=True
)


async def _paper_qa_baseline(
    paper: Paper, question, gold_support: Sequence[str] | None, enumerate_answer: bool
) -> PaperQaAnswer:
    gold_support  # unused
    answer: str | Sequence[str]
    all_paras = [str(p).casefold().strip() for p in paper.paragraphs if str(p).strip()]
    answer, predicted_paras = await answer_for_paper(paper, question, top_n=1)
    predicted_paras = [p.casefold().strip() for p in predicted_paras]
    if enumerate_answer:
        answer = await quick_list(question, answer)
    return PaperQaAnswer(
        answer=answer,
        support_candidates=all_paras,
        support_labels=[p.casefold().strip() in predicted_paras for p in all_paras],
    )


paper_qa_baseline_str_answer: PaperQaMethod[str] = partial(
    _paper_qa_baseline, enumerate_answer=False
)
paper_qa_baseline_list_answer: PaperQaMethod[Sequence[str]] = partial(
    _paper_qa_baseline, enumerate_answer=True
)


async def _demonstration_answer(
    question: str,
    texts: Sequence[str],
    demonstrations: Sequence[Demonstration],
    reasoning: bool,
):
    try:
        if not reasoning:
            return await demonstration_answer(
                question=question, texts=texts, demonstrations=demonstrations
            )
        else:
            return await demonstration_answer_with_reasoning(
                question=question, texts=texts, demonstrations=demonstrations
            )
    except TooLongRequestError:
        demonstrations = demonstrations[:-1]
        if len(demonstrations) < 1:
            raise
        return await _demonstration_answer(
            question=question,
            texts=texts,
            demonstrations=demonstrations,
            reasoning=reasoning,
        )


async def preselected_few_shot_qa_baseline(
    paper: Paper,
    question: str,
    gold_support: Sequence[str] | None,
    enumerate_answer: bool,
    few_shot_demonstration_func: Callable[[str], Sequence[PaperQaGoldStandard]],
    selections: Sequence[str] | None = None,
    paper_division_func: Callable[[Paper], Sequence[str]] | None = None,
    reasoning: bool = False,
):
    demonstration_examples = few_shot_demonstration_func(paper.document_id)
    if paper_division_func:
        demonstration_examples = await map_async(
            demonstration_examples,
            partial(
                convert_demonstration_example,
                paper_division_func=paper_division_func,
            ),
        )
    demonstration_examples = [ex for ex in demonstration_examples if ex.gold_support][
        :3
    ]
    demonstrations = [
        Demonstration(
            question=g.question,
            texts=g.gold_support,
            answer=g.gold_answer
            if isinstance(g.gold_answer, str)
            else numbered_list(g.gold_answer).transform(),
        )
        for g in demonstration_examples
    ]
    if paper_division_func and gold_support:
        gold_support = await identify_gs_str(paper_division_func(paper), gold_support)
    support = gold_support or selections
    assert support
    answer = await _demonstration_answer(
        question=question,
        texts=support,
        demonstrations=demonstrations,
        reasoning=reasoning,
    )

    if enumerate_answer:
        answer = await quick_list(question, answer)
    if paper_division_func:
        support_candidates = paper_division_func(paper)
        support_labels = as_bool(support, support_candidates)
    else:
        support_labels = [False for _ in support]

    return PaperQaAnswer(
        answer=answer,
        support_candidates=support,
        support_labels=support_labels,
    )


# Refactoring notes
# for evaling more structured recipe return types, pass in the evaluation function
# specify the question short name; we need somewhere a mapping of these to the ModelType
#

# to specify an experiment from the command line (or perhaps better a file)
# - recipe function (paper, question, gold_support | None) -> PaperQaAnswer (answer, support)
# - generator of (paper, question, gold_support | None) from parsed golds (question_and_answer_func)
# - split (+ slice?) and/or files
# - question_short_name (has an implied ModelType that must match question_and_answer_func)
# - eval function (where the return type matches the output of the recipe function)


recipe.main(cheating_qa_baseline_str_answer)
