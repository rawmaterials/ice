from typing import Any
from typing import Literal

from structlog.stdlib import get_logger

from ice.agents.base import Agent
from ice.apis.wolfram import wolfram_answer
from ice.environment import env

log = get_logger()


API_ENDPOINT = "result"
UNITS = Literal["metric", "imperial"]


class WolframAgent(Agent):
    """An agent that uses the Wolfram|Alpha Short Answers API to generate answers."""

    def __init__(self, timeout: float | None = None):
        self.timeout = timeout

    async def answer(
        self,
        *,
        question: str,
        units: UNITS | None = None,
        verbose: bool = False,
    ) -> str:
        """Generate a short answer to the given question."""
        if verbose:
            self._print_markdown(question)
        response = await self._answer(question, units=units)
        answer = self._extract_answer(response)
        if verbose:
            self._print_markdown(answer)
        return answer

    async def _answer(
        self,
        question,
        units: UNITS | None = None,
        **kwargs
    ) -> dict:
        """Send a request to the Wolfram|Alpha API with the given question and parameters."""
        if self.timeout is not None:
            kwargs["timeout"] = self.timeout
        if units is not None:
            kwargs["units"] = units

        response = await wolfram_answer(
            question=question,
            endpoint=API_ENDPOINT,
            **kwargs
        )
        return response

    def _extract_answer(self, response: dict) -> str:
        """Extract the answer text from the response."""
        return response["result"]

    def _print_markdown(self, obj: Any):
        """Print the text with markdown formatting."""
        env().print(obj, format_markdown=True)
