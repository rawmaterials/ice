import httpx
import urllib

from httpx import TimeoutException
from structlog.stdlib import get_logger
from tenacity import retry
from tenacity.retry import retry_any
from tenacity.retry import retry_if_exception
from tenacity.retry import retry_if_exception_type
from tenacity.wait import wait_random_exponential

from ice.cache import diskcache
from ice.settings import settings

log = get_logger()


class RateLimitError(Exception):
    def __init__(self, response: httpx.Response):
        self.response = response
        try:
            message = response.json()["error"]["message"]
        except Exception:
            message = response.text[:100]
        super().__init__(message)


def log_attempt_number(retry_state):
    if retry_state.attempt_number > 1:
        exception = retry_state.outcome.exception()
        exception_name = exception.__class__.__name__
        exception_message = str(exception)
        log.warning(
            f"Retrying ({exception_name}: {exception_message}): "
            f"Attempt #{retry_state.attempt_number}..."
        )


RETRYABLE_STATUS_CODES = {408, 429, 502, 503, 504}
WOLFRAM_BASE_URL = "http://api.wolframalpha.com/v1/"
WOLFRAM_CONTINUATION_URL_TEMPLATE = "http://{host}/api/v1"


def is_retryable_HttpError(e: BaseException) -> bool:
    return (
        isinstance(e, httpx.HTTPStatusError)
        and e.response.status_code in RETRYABLE_STATUS_CODES
    )


@retry(
    retry=retry_any(
        retry_if_exception(is_retryable_HttpError),
        retry_if_exception_type(TimeoutException),
        retry_if_exception_type(RateLimitError),
    ),
    wait=wait_random_exponential(min=1),
    after=log_attempt_number,
)
async def _post(
    host: str,
    endpoint: str,
    query_string: str,
    timeout: float | None = None
) -> dict:
    """Send a POST request to the Wolfram|Alpha API and return the JSON response."""

    async with httpx.AsyncClient() as client:
        host_url = WOLFRAM_BASE_URL \
            if host is None \
            else WOLFRAM_CONTINUATION_URL_TEMPLATE.replace("{host}", host)
        response = await client.post(
            f"{host_url}/{endpoint}?{query_string}",
            timeout=timeout,
        )
        if response.status_code == 429:
            raise RateLimitError(response)
        if response.status_code == 400:
            raise ValueError("Must provide a valid value for the input parameter")
        if response.status_code == 501:
            raise KeyError("Must provide an input parameter")
        response.raise_for_status()
        if endpoint == "result":
            return {
                "result": response.text
            }
        else:
            return response.json()


def _make_query_string(question: str, **kwargs) -> str:
    url_encoded_question = urllib.parse.quote_plus(question)
    query_string = f"appid={settings.WOLFRAM_API_KEY}&i={url_encoded_question}"
    for arg in kwargs:
        query_string += f"&{arg}={kwargs[arg]}"
    return query_string


@diskcache()
async def wolfram_answer(
    question: str,
    endpoint: str,
    host: str | None = None,
    cache_id: int = 0,  # for repeated non-deterministic sampling using caching
    **kwargs,
) -> dict:
    """Send an answer request to the Wolfram|Alpha API and return the JSON response."""
    cache_id  # unused
    query_string = _make_query_string(question, **kwargs)
    return await _post(
        host=host,
        endpoint=endpoint,
        query_string=query_string,
    )
