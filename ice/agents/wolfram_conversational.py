from typing import Any
from typing import Literal

from structlog.stdlib import get_logger

from ice.agents.base import Agent
from ice.apis.wolfram import wolfram_answer
from ice.environment import env

log = get_logger()


API_ENDPOINT = "conversation.jsp"
UNITS = Literal["metric", "imperial"]


class WolframConversationalAgent(Agent):
    """An agent that uses the Wolfram|Alpha Conversational API to generate answers."""

    def __init__(
        self,
        geolocation: str | None = None,
        ip: str | None = None,
    ):
        self.geolocation = geolocation
        self.ip = ip
        self.conversation_id = None
        self.host = None
        self.s = None

    async def answer(
        self,
        *,
        question: str,
        units: UNITS | None = None,
        verbose: bool = False,
    ) -> str:
        """Generate an answer to the given question."""
        if verbose:
            self._print_markdown(question)
        response = await self._answer(question, units=units)

        if "error" in response:
            raise Exception(response["error"])

        self._extract_parameters_for_next_question(response)

        answer = self._extract_answer(response)
        if verbose:
            self._print_markdown(answer)
        return answer

    async def _answer(
        self,
        question,
        units: UNITS | None = None,
    ) -> dict:
        """Send an answer request to the Wolfram|Alpha API with the given question and parameters."""

        parameters = self._get_parameters(units=units)

        response = await wolfram_answer(
            question=question,
            endpoint=API_ENDPOINT,
            host=self.host,
            **parameters
        )
        return response

    def _extract_parameters_for_next_question(self, response: dict):
        if "conversationID" in response:
            self.conversation_id = response["conversationID"]
        if "host" in response:
            self.host = response["host"]
        if "s" in response:
            self.s = response["s"]

    def _get_parameters(self, units: UNITS | None = None) -> dict:
        parameters = {}
        if self.geolocation is not None:
            parameters["geolocation"] = self.geolocation
        if self.ip is not None:
            parameters["ip"] = self.ip
        if self.conversation_id is not None:
            parameters["conversationid"] = self.conversation_id
        if self.s is not None:
            parameters["s"] = self.s
        if units is not None:
            parameters["units"] = units
        return parameters

    def _extract_answer(self, response: dict) -> str:
        """Extract the answer text from the response."""
        return response["result"]

    def _print_markdown(self, obj: Any):
        """Print the text with markdown formatting."""
        env().print(obj, format_markdown=True)
