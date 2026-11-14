"""
dlt source for concise violence/gore summaries via the Mistral Conversations API.

For every movie in ``movie_catalogue``, starts a Mistral conversation with
the server-side ``web_search`` tool enabled and asks for a concise violence
and gore summary using fixed severity and frequency labels. The final
assistant message is stored together with tool-reference citations as
provenance.

``web_search`` is only available on the Conversations/Agents API
(``/v1/conversations``), not in chat completions. Each run re-analyses the
full catalogue (no skip logic); ``scraped_at`` marks the snapshot.

Secrets
-------
Resolved from environment variables (loaded via ``.env``):

    SOURCES__MISTRAL__API_KEY
"""

# dlt config section: resolves [sources.mistral] config and
# SOURCES__MISTRAL__* env keys independently of the source rename.
__source_name__ = "mistral"

import logging
import time
from datetime import datetime, timezone
from typing import Iterator

import dlt
import requests
from dlt.common.typing import TDataItems

from ingestion.sources.api.omdb.main import read_movie_catalogue

REQUEST_DELAY = 0.5  # Delay between API requests to avoid rate limiting
DEFAULT_MODEL = "mistral-medium-latest"
CONVERSATIONS_PATH = "/conversations"

logger = logging.getLogger(__name__)

INSTRUCTIONS = (
    "You research movies using web search and answer with concise, "
    "factual content notes. When you cannot find pertinent information "
    "about a movie, say so plainly instead of guessing."
)

SUMMARY_PROMPT_TEMPLATE = """\
Web search the movie '{title}' released on {release_date} to determine the \
severity and frequency of its violence and gore content based on information \
available through reviews, articles and comments of the movie. Match the film \
title and date in case there is more than one movie with the same title. If \
you cannot find any pertinent information on the movie then state that you \
are unable to find it.

Answer with a concise violence/gore summary (a few sentences) that ends with \
exactly one severity label and one frequency label chosen from the tables \
below. For example in this system, Terrifier would be extreme and pervasive, \
the Shining high and occasional, and Lake Mungo mild and isolated.

Severity labels:

| Severity Label | Keywords/Descriptors |
| --- | --- |
| Mild | Minor injuries, implied violence, no blood |
| Moderate | Blood, injuries, some gore |
| High | Graphic injuries, mutilation, psychological |
| Extreme | Dismemberment, torture, cannibalism, rituals |

Frequency labels:

| Frequency Label | Definition |
| --- | --- |
| Isolated | 1-2 brief or minor instances of violence/gore. |
| Occasional | 3-5 scenes, or violence/gore is present but not central to the plot. |
| Frequent | 6+ scenes, or violence/gore is a recurring element. |
| Pervasive | Violence/gore is constant, central to the plot, or described as overwhelming. |
"""


def summarize_violence_gore(
    title: str,
    release_date: str,
    api_key: str,
    base_url: str,
    model: str = DEFAULT_MODEL,
) -> dict:
    """
    Request a concise violence/gore summary for one movie from Mistral.

    Starts a fresh conversation with the ``web_search`` tool enabled,
    passing the model, instructions and tool inline rather than creating
    a stored agent — the Conversations API accepts them directly, which
    avoids accumulating server-side agents across runs.

    Parameters
    ----------
    title : str
        The title of the movie to analyze.
    release_date : str
        The release date of the movie in YYYY-MM-DD format.
    api_key : str
        Mistral API key sent as a bearer token.
    base_url : str
        Mistral API base URL (e.g. ``https://api.mistral.ai/v1``).
    model : str, optional
        Mistral model name. Default is ``mistral-medium-latest``.

    Returns
    -------
    dict
        Keys ``summary`` (text of the final assistant message) and
        ``citations`` (list of dicts with ``title`` and ``url`` from
        ``tool_reference`` chunks; empty when nothing was cited).

    Raises
    ------
    ValueError
        If the API key is missing or the response has no assistant
        message.
    requests.HTTPError
        If the API returns a non-2xx status code.
    """
    if not api_key:
        raise ValueError("SOURCES__MISTRAL__API_KEY environment variable is not set")

    payload = {
        "model": model,
        "instructions": INSTRUCTIONS,
        "tools": [{"type": "web_search"}],
        "store": False,
        "inputs": SUMMARY_PROMPT_TEMPLATE.format(title=title, release_date=release_date),
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    response = requests.post(
        f"{base_url}{CONVERSATIONS_PATH}",
        json=payload,
        headers=headers,
        timeout=120,
    )
    response.raise_for_status()
    time.sleep(REQUEST_DELAY)

    outputs = response.json().get("outputs", [])
    message_outputs = [entry for entry in outputs if entry.get("type") == "message.output"]
    if not message_outputs:
        raise ValueError("Unexpected API response structure: no 'message.output' entry")
    return parse_message_content(message_outputs[-1].get("content"))


def parse_message_content(content: str | list[dict]) -> dict:
    """
    Split a conversation message body into summary text and citations.

    Message content is either a plain string or a list of typed chunks.
    ``text`` chunks carry the summary; ``tool_reference`` chunks carry
    web-search provenance (title and URL); everything else (thinking
    chunks, images, tool files) is ignored.

    Parameters
    ----------
    content : str or list
        The ``content`` field of a ``message.output`` entry.

    Returns
    -------
    dict
        Keys ``summary`` (concatenated ``text`` chunks) and ``citations``
        (list of dicts with ``title`` and ``url``).
    """
    if isinstance(content, str):
        return {"summary": content, "citations": []}

    summary_chunks: list[str] = []
    citations: list[dict] = []
    for chunk in content:
        chunk_type = chunk.get("type")
        if chunk_type == "text":
            summary_chunks.append(chunk.get("text", ""))
        elif chunk_type == "tool_reference":
            citations.append({"title": chunk.get("title"), "url": chunk.get("url")})
    return {"summary": "".join(summary_chunks), "citations": citations}


@dlt.source(name="violence_gore_summary")
def violence_gore_summary_source(
    api_key: str = dlt.secrets.value,
    base_url: str = dlt.config.value,
    model: str = DEFAULT_MODEL,
):
    """
    Violence/gore summary source: one Mistral conversation per catalogue movie.

    Reads the movie catalogue from the pipeline destination and requests a
    concise violence/gore summary for every film. Each run re-analyses the
    full catalogue; there is no completion tracking.

    Writes to table: ``violence_gore_summary`` (append-only) with a
    ``violence_gore_summary__citations`` child table for provenance.

    Parameters
    ----------
    api_key : str
        Mistral API key. Resolved from env var ``SOURCES__MISTRAL__API_KEY``.
    base_url : str
        Mistral API base URL. Resolved from ``.dlt/config.toml``.
    model : str, optional
        Mistral model name. Default is ``mistral-medium-latest``;
        overridable via a ``model`` entry in the ``[sources.mistral]``
        config section.
    """

    @dlt.resource(name="violence_gore_summary", write_disposition="append")
    def violence_gore_summary() -> Iterator[TDataItems]:
        """
        Yield a violence/gore summary row for every movie in the catalogue.
        """
        movies = read_movie_catalogue()
        scraped_at = datetime.now(timezone.utc)

        for movie in movies:
            title = movie.get("title") or movie.get("original_title", "")
            release_date = movie.get("release_date", "")
            try:
                result = summarize_violence_gore(
                    title=title,
                    release_date=release_date,
                    api_key=api_key,
                    base_url=base_url,
                    model=model,
                )
            except requests.RequestException as error:
                logger.error("Mistral request failed for %s: %s", title, error)
                continue

            yield {
                "title": title,
                "release_date": release_date,
                "tmdb_id": movie.get("id"),
                "model": model,
                "summary": result["summary"],
                "citations": result["citations"],
                "scraped_at": scraped_at,
            }

    return violence_gore_summary
