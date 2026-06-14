import os
from datetime import datetime, timezone
from typing import Dict, Iterator

import dlt
import requests

# Constants
REQUEST_DELAY = 0.5  # Delay between API requests to avoid rate limiting

# Function to send request to Mistral API


def get_violence_gore_analysis(title: str, release_date: str) -> Dict:
    """
    Send a request to the Mistral API to get violence/gore severity and frequency.

    Parameters
    ----------
    title : str
        The title of the movie to analyze.
    release_date : str
        The release date of the movie in YYYY-MM-DD format.

    Returns
    -------
    Dict
        A dictionary containing the violence/gore analysis results.

    Raises
    ------
    requests.HTTPError
        If the API request fails.
    """
    # Define the prompt for the Mistral API

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
    | Isolated | 1–2 brief or minor instances of violence/gore. | "One scene of blood," "a character is pushed," "a single gunshot" |
    | Occasional | 3–5 scenes, or violence/gore is present but not central to the plot. | "Several scenes of blood," "some violent confrontations," "a few gory moments" |
    | Frequent | 6+ scenes, or violence/gore is a recurring element. | "Many scenes of bloodshed," "repeated torture," "violence throughout the film" |
    | Pervasive | Violence/gore is constant, central to the plot, or described as overwhelming. | "Constant gore," "non-stop violence," "the entire film is filled with disturbing scenes" |
    """

    # API endpoint and parameters
    url = "https://api.anthropic.com/v1/messages"
    params = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    }

    headers = {
        "x-api-key": os.environ["ANTHROPIC_API_KEY"],
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    # Make the API request
    response = requests.post(url, json=params, headers=headers)
    response.raise_for_status()

    # Extract and return the response content
    response_data = response.json()
    return response_data["content"][0]["text"]


# Main pipeline function


def run_movie_analysis_pipeline() -> None:
    """
    Main function to run the dlt pipeline that extracts movie data and sends requests to the Claude API.

    This function initializes the pipeline, defines the resources for movie data and violence/gore analysis,
    and runs the pipeline to process the data.

    Returns
    -------
    None
    """
    # Initialize the pipeline
    pipeline = dlt.pipeline(
        pipeline_name="violence_gore_analysis",
        destination="motherduck",
        dataset_name="raw",
    )

    # Define the resource for violence/gore analysis
    @dlt.resource(name="violence_gore_analysis", write_disposition="append")
    def violence_gore_analysis(batch_size: int = 300) -> Iterator[Dict]:
        """
        Resource to send requests to Claude API for violence/gore analysis.
        Processes movies in batches of specified size.

        Parameters
        ----------
        batch_size : int
            Maximum number of movies to process in single pipeline run.
        """
        # Get all movies from raw.movie_catalogue
        query = """
        SELECT title, release_date
        FROM raw.movie_catalogue
        """
        with pipeline.sql_client() as client:
            # Get all movies
            with client.execute_query(query) as cursor:
                all_movies = {(row[0], row[1]) for row in cursor.fetchall()}

            # Get already processed movies (table may not exist on first run)
            processed_movies = set()
            try:
                processed_query = """
                SELECT title, release_date
                FROM raw.violence_gore_analysis
                """
                with client.execute_query(processed_query) as cursor:
                    processed_movies = {(row[0], row[1]) for row in cursor.fetchall()}
            except:
                pass  # Table doesn't exist yet, so no movies processed

            # Get unprocessed movies and limit to batch size
            unprocessed_movies = all_movies - processed_movies

            # Process first batch_size movies
            for title, release_date in list(unprocessed_movies)[:batch_size]:
                try:
                    analysis = get_violence_gore_analysis(title, release_date)
                    yield {
                        "title": title,
                        "release_date": release_date,
                        "model": "claude-sonnet-4-6",
                        "model_response": analysis,
                        "timestamp": datetime.now(timezone.utc),
                    }
                except Exception as e:
                    print(f"Error analyzing movie {title}: {e}")
                    continue

    # Run the pipeline
    load_info = pipeline.run([violence_gore_analysis()])

    print(f"Pipeline run completed: {load_info}")
