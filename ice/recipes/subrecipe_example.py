from structlog import get_logger

from ice.recipe import Recipe

log = get_logger()


class MetaRecipe(Recipe):
    async def run(self, input: list[str]) -> list[str]:
        assert input, "MetaRecipe requires an 'input' argument"

        async def first_node():
            output = input + ["MetaRecipe.first_node"]
            return output

        async def second_node(pred: list[str]):
            output = pred + ["MetaRecipe.second_node"]
            return output

        return await second_node(pred=(await first_node()))


class ExampleMetaRecipe(Recipe):
    async def run(self):
        other_recipe = MetaRecipe(mode=self.mode)
        sub_result = await other_recipe.run(input=["MetaRecipe"])
        final_result = sub_result + ["MetaRecipe.collect_result"]
        return " ---> ".join(final_result)
