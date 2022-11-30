
from pathlib import Path

from ice import execution_context
from ice.evaluation.evaluate_recipe_result import RecipeResult
from ice.evaluation.metrics.gold_standards import retrieve_gold_standards_df
from ice.paper import Paper
from ice.recipe import Recipe
from ice.utils import map_async


class RecipeExecutor:
    def __init__(
        self,
        recipe: Recipe,
        input_files: list[str] | None = None,
        gold_standard_splits: list[str] | None = None,
        question_short_name: str | None = None,
    ):
        if (gold_standard_splits is None) != (question_short_name is None):
            raise ValueError(
                "Must specify both gold_standard_splits and question_short_name or neither."
            )

        self.recipe = recipe
        self.input_files = input_files
        self.gold_standard_splits = gold_standard_splits
        self.question_short_name = question_short_name


    async def _get_papers(self) -> list[Paper]:
        """
        Get the list of papers based on the user input or selection.
        """

        if self.input_files:
            paper_files = [Path(i) for i in self.input_files]
        elif self.gold_standard_splits:
            gs_df = retrieve_gold_standards_df()
            question_gs_in_splits = gs_df[
                (gs_df.question_short_name == self.question_short_name)
                & (gs_df.split.isin(self.gold_standard_splits))
                & (gs_df["Are quotes enough?"] != "No")
            ]
            paper_dir = Path(__file__).parent / "papers/"
            paper_files = [
                f
                for f in paper_dir.iterdir()
                if f.name in question_gs_in_splits.document_id.unique()
            ]
        else:
            paper_files = []

        # If user doesn't specify papers via CLI args, we could prompt them
        # but this makes it harder to run recipes that don't take papers as
        # arguments, so we won't do that here.

        # if self.input_files is None and self.gold_standard_splits is None:
        #     paper_names = [f.name for f in paper_files]
        #     selected_paper_names = await env().checkboxes("Papers", paper_names)
        #     paper_files = [f for f in paper_files if f.name in selected_paper_names]

        return [Paper.load(f) for f in paper_files]


    async def get_results(self, args: dict) -> dict[str, RecipeResult]:
        """
        Run the recipe over the papers and return a map from paper ids to recipe results.
        """

        papers = await self._get_papers()

        if papers:
            print(
                f"Running recipe {self.recipe} over papers {', '.join(p.document_id for p in papers)}"
            )
        else:
            # Run recipe without paper arguments
            result = await self.recipe.run(**args)
            return {
                "No paper": result
            }

        async def apply_recipe_to_paper(paper: Paper) -> RecipeResult:
            execution_context.new_context(document_id=paper.document_id, task=str(self.recipe))
            return await self.recipe.run(paper=paper, **args)

        # Run recipe over papers
        max_concurrency = 5 if self.recipe.mode == "machine" else 1
        results = await map_async(
            papers,
            apply_recipe_to_paper,
            show_progress_bar=True,
            max_concurrency=max_concurrency,
        )

        return {
            paper.document_id: result for (paper, result) in zip(papers, results)
        }
