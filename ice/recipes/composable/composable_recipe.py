from ice.recipe import recipe
from ice.recipe import FunctionBasedRecipe
from ice.recipes.composable.question_strategy import *


class ComposableRecipe:
    def __init__(
        self,
        r: FunctionBasedRecipe,
        question_strategy: QuestionStrategy,
        question: str,
        context: str = "",
    ):
        self.recipe = r
        self.question_strategy = question_strategy
        self.question = question
        self.context = context

    async def compose(
        self,
        r: FunctionBasedRecipe,
    ) -> "ComposableRecipe":
        answer = await self.get_answer()
        self.context += f"Q. {self.question}\nA. {answer}\n\n"
        next_question = self.question_strategy.follow_up_question(self.context)
        return ComposableRecipe(
            r=r,
            question_strategy=self.question_strategy,
            question=next_question,
            context=self.context
        )

    async def get_answer(self):
        context = f"{self.context}Given the above questions and answers, answer the following question.\n\n" if self.context else ""
        question_with_context = f"{context}{self.question}"
        return await self.recipe(question=question_with_context)


# Mock recipes

async def openai_answer(question: str):
    return await recipe.agent().complete(prompt=question, stop='"')

async def wolfram_answer(question: str):
    return await recipe.agent("wolfram-conversational").answer(question=question)


async def answer_with_elaboration(
    question: str = "Can you give a description of the Holy Roman Empire?"
):
    question_strategy = ElaborateQuestionStrategy()
    composable_recipe = ComposableRecipe(
                            r=wolfram_answer,
                            question_strategy=question_strategy,
                            question=question
                        )
    composable_recipe = await composable_recipe.compose(openai_answer)
    return await composable_recipe.get_answer()


recipe.main(answer_with_elaboration)
