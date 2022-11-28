#! /usr/bin/env python
import asyncio
import json

import defopt

from structlog.stdlib import get_logger

from ice.main.recipe_executor import RecipeExecutor
from ice.main.recipe_fetcher import get_recipe
from ice.main.results_writer import ResultsWriter
from ice.mode import Mode
from ice.trace import enable_trace
from ice.trace import trace


log = get_logger()


def main_cli(
    *,
    mode: Mode = "machine",
    output_file: str | None = None,
    json_out: str | None = None,
    recipe_name: str | None = None,
    input_files: list[str] | None = None,
    gold_standard_splits: list[str] | None = None,
    question_short_name: str | None = None,
    trace: bool = True,
    args: dict | None = None,
):
    """
    ::
    Run a recipe.
    :param mode Mode:  Mode to run the recipe in (default: "machine").
    :param output_file:  Append output to a file in Markdown format instead of stdout.
    :param json_out:  Write recipe-specific JSON output to a file.
    :param recipe_name:  Name of the recipe to run.
    :param input_files:  List of files to run recipe over.
    :param gold_standard_splits:  "iterate", "validation", and/or "test".
    :param question_short_name:  "question_short_name" column value to filter by.
    :param trace:  Generate a trace file (default: true).
    :param args:  Arguments to pass to the recipe.
    """
    if trace:
        enable_trace()

    async def main_wrapper():
        # A traced function cannot be called until the event loop is running.
        return await main(
            mode=mode,
            output_file=output_file,
            json_out=json_out,
            recipe_name=recipe_name,
            input_files=input_files,
            gold_standard_splits=gold_standard_splits,
            question_short_name=question_short_name,
            args=args or {},
        )

    asyncio.run(main_wrapper())


@trace
async def main(
    *,
    mode: Mode,
    output_file: str | None,
    json_out: str | None,
    recipe_name: str | None,
    input_files: list[str] | None,
    gold_standard_splits: list[str] | None,
    question_short_name: str | None,
    args: dict,
):
    recipe = await get_recipe(recipe_name, mode)

    recipe_executor = RecipeExecutor(
                          recipe=recipe,
                          input_files=input_files,
                          gold_standard_splits=gold_standard_splits,
                          question_short_name=question_short_name,
                      )

    # Run recipe over papers
    results = await recipe_executor.get_results(args)

    results_writer = ResultsWriter(
                         recipe=recipe,
                         results=results,
                     )

    # Print results
    await results_writer.print_results(output_file)

    if json_out is not None:
        await results_writer.write_results_json(json_out)

    # Print evaluation of results
    await results_writer.print_and_write_evaluation_results(output_file)


if __name__ == "__main__":
    defopt.run(main_cli, parsers={dict: json.loads})
