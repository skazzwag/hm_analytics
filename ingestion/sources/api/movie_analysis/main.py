"""
dlt source for violence/gore analysis via the Anthropic API.

Sends movies that have not yet been analysed to Claude and stores the raw
severity/frequency assessment. Movies already present in the destination
table are skipped, so repeated runs make forward progress in batches.

Secrets
-------
Resolved from environment variables (loaded via ``.env``):

    SOURCES__ANTHROPIC__API_KEY
"""

import logging
from datetime import datetime, timezone
from typing import Iterator

import dlt
import requests
from dlt.common.typing import TDataItems

REQUEST_DELAY = 0.5  # Delay between API requests to avoid rate limiting

ANALYSIS_MODEL = "claude-sonnet-4-6"

logger = logging.getLogger(__name__)


def get_violence_gore_analysis(
    title: str,
    release_date: str,
    api_key: str,
    base_url: str,
) -> str:
    """
    Send a request to the Anthropic API to get violence/gore severity and frequency.

    Parameters
    ----------
    title : str
        The title of the movie to analyze.
    release_date : str
        The release date of the movie in YYYY-MM-DD format.
    api_key : str
        Anthropic API key sent as the ``x-api-key`` header.
    base_url : str
        Anthropic API base URL (e.g. ``https://api.anthropic.com/v1``).

    Returns
    -------
    str
        The raw model response text.

    Raises
    ------
    requests.HTTPError
        If the API request fails.
    ValueError
        If the API key is missing or the response has an unexpected shape.
    """
    prompt = f"""
    Web search the movie '{title}' released on {release_date} to determine the severity and frequency of its violence and gore content based on information available through reviews, articles and comments of the movie.
    Make sure that you match the film title and date in case there's more than one movie with the same date. If you cannot find any pertinent information on the movie then state that you are unable to find it. Ensure that you only use one label for severity and one label for frequency, shown in the tables below

    For level of violence/gore use the following rating system. Ensure that only a single severity label is given. As an example in this system, Terrifier would be extreme, The Shining is high, and Lake Mungo would be mild.

    | Severity Label | Keywords/Descriptors | Example |
    | --- | --- | --- |
    | Mild | Minor injuries, implied violence, no blood | "A character is pushed to the ground" |
    | Moderate | Blood, injuries, some gore | "A character is stabbed; blood shown" |
    | High | Graphic injuries, mutilation, psychological | "A face is unrecognizably mutilated" |
    | Extreme | Dismemberment, torture, cannibalism, rituals | "Lungs pulled out through the back" |

    For frequency of violence/gore use the following rating system. Ensure that only a single frequency label is given. As an example in this system, Terrifier would be pervasive, The Shining is occasional, and Lake Mungo would be isolated.

    | Frequency Label | Definition | Example Descriptors in Parents Guide |
    | --- | --- | --- |
    | Isolated | 1-2 brief or minor instances of violence/gore. | "One scene of blood," "a character is pushed," "a single gunshot" |
    | Occasional | 3-5 scenes, or violence/gore is present but not central to the plot. | "Several scenes of blood," "some violent confrontations," "a few gory moments" |
    | Frequent | 6+ scenes, or violence/gore is a recurring element. | "Many scenes of bloodshed," "repeated torture," "violence throughout the film" |
    | Pervasive | Violence/gore is constant, central to the plot, or described as overwhelming. | "Constant gore," "non-stop violence," "the entire film is filled with disturbing scenes" |
    """

    if not api_key:
        raise ValueError("SOURCES__ANTHROPIC__API_KEY environment variable is not set")

    # API endpoint and parameters
    url = f"{base_url}/messages"
    params = {
        "model": ANALYSIS_MODEL,
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    }

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    # Make the API request
    response = requests.post(url, json=params, headers=headers)
    response.raise_for_status()

    # Extract and return the response content
    response_data = response.json()
    if not response_data.get("content") or not response_data["content"]:
        raise ValueError("Unexpected API response structure: missing 'content' field")

    return response_data["content"][0]["text"]


@dlt.source(name="anthropic")
def movie_analysis_source(
    api_key: str = dlt.secrets.value,
    base_url: str = dlt.config.value,
    batch_size: int = 300,
):
    """
    Violence/gore analysis source for unprocessed movies via the Anthropic API.

    Reads the movie catalogue and any prior analyses from the pipeline
    destination, then sends the first ``batch_size`` unprocessed movies to
    Claude for a violence/gore assessment.

    Parameters
    ----------
    api_key : str
        Anthropic API key. Resolved from env var ``SOURCES__ANTHROPIC__API_KEY``.
    base_url : str
        Anthropic API base URL. Resolved from ``.dlt/config.toml``.
    batch_size : int
        Maximum number of movies to process in a single pipeline run.
    """

    # Define the resource for violence/gore analysis
    @dlt.resource(name="violence_gore_analysis", write_disposition="append")
    def violence_gore_analysis() -> Iterator[TDataItems]:
        """
        Send requests to the Anthropic API for violence/gore analysis.
        """
        pipeline = dlt.current.pipeline()

        with pipeline.sql_client() as client:
            # Get all movies
            catalogue_query = """
            SELECT title, release_date
            FROM raw.movie_catalogue
            """
            with client.execute_query(catalogue_query) as cursor:
                all_movies = {(row[0], row[1]) for row in cursor.fetchall()}

            # Get already processed movies (table may not exist on first run)
            processed_movies: set[tuple[str, str]] = set()
            try:
                processed_query = """
                SELECT title, release_date
                FROM raw.violence_gore_analysis
                """
                with client.execute_query(processed_query) as cursor:
                    processed_movies = {(row[0], row[1]) for row in cursor.fetchall()}
            except Exception as error:
                logger.warning(
                    "Table doesn't exist yet, so no movies processed: %s", error
                )

            # Get unprocessed movies and limit to batch size
            unprocessed_movies = all_movies - processed_movies

            # Process first batch_size movies (sorted for deterministic batches)
            for title, release_date in sorted(unprocessed_movies)[:batch_size]:
                try:
                    analysis = get_violence_gore_analysis(
                        title, release_date, api_key, base_url
                    )
                    yield {
                        "title": title,
                        "release_date": release_date,
                        "model": ANALYSIS_MODEL,
                        "model_response": analysis,
                        "timestamp": datetime.now(timezone.utc),
                    }
                except Exception as error:
                    logger.error("Error analyzing movie %s: %s", title, error)
                    continue

    return violence_gore_analysis
