import json

from ice.environment import env
from ice.evaluation.evaluate_recipe_result import RecipeResult
from ice.recipe import is_list_of_recipe_result
from ice.recipe import Recipe


class ResultsWriter:
    def __init__(
        self,
        recipe: Recipe,
        results: dict[str, RecipeResult],
    ):
        self.recipe = recipe
        self.results = results


    async def print_results(
        self,
        output_file: str | None,
    ):
        """Print the results to the output file or stdout."""

        for (document_id, final_result) in self.results.items():
            env().print(
                f"## Final result for {document_id}\n",
                format_markdown=False if output_file else True,
                wait_for_confirmation=False,
                file=output_file,
            )

            if is_list_of_recipe_result(final_result):
                results_to_print = [r.result for r in final_result]
            else:
                results_to_print = [final_result]

            for result_to_print in results_to_print:
                env().print(
                    result_to_print,
                    format_markdown=False,
                    wait_for_confirmation=False,
                    file=output_file,
                )


    async def write_results_json(
        self,
        json_out: str,
    ):
        """Write the JSON representation of the results."""

        results_json: list[dict] = []

        for (document_id, final_result) in self.results.items():
            results_json.extend(self.recipe.to_json(final_result))

        with open(json_out, "w") as f:
            json.dump(results_json, f, indent=2)


    async def print_and_write_evaluation_results(
        self,
        output_file: str | None,
    ):
        """
        Evaluate the results using the recipe's evaluation report and
        dashboard row methods, and print the report to the output file or
        stdout.
        """

        if self.recipe.results:
            evaluation_report = await self.recipe.evaluation_report()

            env().print(
                evaluation_report,
                format_markdown=False if output_file else True,
                wait_for_confirmation=True,
                file=output_file,
            )

            evaluation_report.make_and_write_dashboard_row_df()
            evaluation_report.make_and_write_experiments_evaluation_df()
