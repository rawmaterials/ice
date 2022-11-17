from ice.recipe import recipe


async def answer(question: str = "How far is Los Angeles from New York?"):
    answer = await recipe.agent("wolfram").answer(question=question)
    return answer


recipe.main(answer)
