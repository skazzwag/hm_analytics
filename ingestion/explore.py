import marimo

__generated_with = "0.20.4"
app = marimo.App(width="medium", app_title="Horror Movie Data Explorer")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Horror Movie Data Explorer

    Post-load inspection of the `horror_movies` DuckDB database.
    Run the ingestion pipeline first:

    ```
    uv run run-ingestion --static --temporal
    ```
    """)
    return


@app.cell
def _():
    import marimo as mo
    import duckdb

    DB_PATH = "horror_movies.duckdb"
    return DB_PATH, duckdb, mo


@app.cell
def _(DB_PATH, duckdb, mo):
    _conn = duckdb.connect(DB_PATH, read_only=True)
    tables_df = _conn.sql("SHOW ALL TABLES").fetchdf()
    _conn.close()
    mo.md(f"### Tables in `raw` dataset\n\n{mo.as_html(tables_df)}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("### Movie catalogue — latest popularity snapshot")
    return


@app.cell
def _(DB_PATH, duckdb):
    _conn = duckdb.connect(DB_PATH, read_only=True)
    catalogue_df = _conn.sql(
        """
        SELECT c.id, c.title, c.release_date, p.vote_average, p.vote_count, p.popularity
        FROM raw.movie_catalogue c
        LEFT JOIN (
            SELECT id, popularity, vote_average, vote_count
            FROM raw.movie_popularity
            WHERE scraped_at = (SELECT MAX(scraped_at) FROM raw.movie_popularity)
        ) p ON c.id = p.id
        ORDER BY p.popularity DESC NULLS LAST
        LIMIT 10
        """
    ).fetchdf()
    _conn.close()
    catalogue_df
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("### Movie details — top by revenue")
    return


@app.cell
def _(DB_PATH, duckdb):
    _conn = duckdb.connect(DB_PATH, read_only=True)
    details_df = _conn.sql(
        """
        SELECT id, title, us_certification, budget, revenue, runtime, genre_names
        FROM raw.movie_details
        ORDER BY revenue DESC NULLS LAST
        LIMIT 10
        """
    ).fetchdf()
    _conn.close()
    details_df
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("### Keywords — most popular movies")
    return


@app.cell
def _(DB_PATH, duckdb):
    _conn = duckdb.connect(DB_PATH, read_only=True)
    keywords_df = _conn.sql(
        """
        SELECT mk.movie_id, c.title, mk.keyword_name
        FROM raw.movie_keywords mk
        JOIN raw.movie_catalogue c ON mk.movie_id = c.id
        ORDER BY c.title
        LIMIT 20
        """
    ).fetchdf()
    _conn.close()
    keywords_df
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("### OMDb scores — latest snapshot, top by IMDb rating")
    return


@app.cell
def _(DB_PATH, duckdb):
    _conn = duckdb.connect(DB_PATH, read_only=True)
    scores_df = _conn.sql(
        """
        SELECT s.tmdb_id, m.title, s.imdb_rating, s.rotten_tomatoes_score,
               s.metascore, s.box_office
        FROM raw.omdb_scores s
        JOIN raw.omdb_metadata m ON s.imdb_id = m.imdb_id
        WHERE s.scraped_at = (SELECT MAX(scraped_at) FROM raw.omdb_scores)
        ORDER BY s.imdb_rating DESC NULLS LAST
        LIMIT 10
        """
    ).fetchdf()
    _conn.close()
    scores_df
    return


if __name__ == "__main__":
    app.run()
