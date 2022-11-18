from ice.recipe import recipe


async def answer(
    questions: list[str] = [
        "What is the size of New York City?",
        "What is its population density?"
    ]
):
    answers = {}
    for question in questions:
        answer = await recipe.agent("wolfram-conversational").answer(question=question)
        answers[question] = answer
    return answers


recipe.main(answer)
