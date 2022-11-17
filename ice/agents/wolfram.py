from typing import Any

from structlog.stdlib import get_logger

from ice.agents.base import Agent
from ice.apis.wolfram import wolfram_answer
from ice.environment import env

log = get_logger()


class WolframAgent(Agent):
    """An agent that uses the Wolfram|Alpha Short Answers API to generate answers."""

    def __init__(self, timeout: float | None = None):
        self.timeout = timeout

    async def answer(
        self,
        *,
        question: str,
        units: str = "",
        verbose: bool = False,
    ) -> str:
        """Generate a short answer to the given question."""
        if verbose:
            self._print_markdown(question)
        answer = await self._answer(question, units=units)
        if verbose:
            self._print_markdown(answer)
        return answer

    async def _answer(self, question, **kwargs) -> dict:
        """Send a request to the Wolfram|Alpha API with the given question and parameters."""
        if self.timeout is not None:
            kwargs["timeout"] = self.timeout

        if kwargs["units"] not in ["metric", "imperial"]:
            del kwargs["units"]

        response = await wolfram_answer(question, **kwargs)
        return response

    def _print_markdown(self, obj: Any):
        """Print the text with markdown formatting."""
        env().print(obj, format_markdown=True)
