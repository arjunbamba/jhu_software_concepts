"""Flask application for browsing admissions analysis results."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import psycopg
from flask import Flask, render_template, request

try:
    from homework_sample_code.course_app.utils import (
        DEFAULT_DB_CONFIG,
        connect,
        import_module,
        managed_connection,
        managed_cursor,
    )
except ModuleNotFoundError:  # pragma: no cover - fallback for ``python app.py``
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from homework_sample_code.course_app.utils import (
        DEFAULT_DB_CONFIG,
        connect,
        import_module,
        managed_connection,
        managed_cursor,
    )


load_data = import_module("load_data")
query_data = import_module("query_data")

try:
    from .main import main
except ImportError:  # pragma: no cover - fallback for direct execution
    main_module = import_module("homework_sample_code.course_app.main")
    main = main_module.main


QuestionAnswers = Dict[str, str]


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_json_to_db = load_data.load_json_to_db
QUESTION_QUERIES = tuple(query_data.QUESTION_QUERIES)

DB_CONFIG = DEFAULT_DB_CONFIG

DATA_FILE = PROJECT_ROOT / "llm_extend_applicant_data.json"


app = Flask(__name__)

is_scraping: bool = False
latest_analysis: QuestionAnswers = {}
data_file: str = str(DATA_FILE)



def _set_scraping(flag: bool) -> None:
    """Mutate the module-level ``is_scraping`` flag.

    :param bool flag: Desired state of the scraping indicator.
    :return: ``None``
    :rtype: None
    """

    globals()["is_scraping"] = flag


def _update_latest_analysis(payload: QuestionAnswers) -> None:
    """Persist the latest analysis snapshot for reuse across requests.

    :param QuestionAnswers payload: Mapping of question labels to answers.
    :return: ``None``
    :rtype: None
    """

    globals()["latest_analysis"] = dict(payload)


def _database_url() -> str:
    """Return the configured database URL.

    :return: Database connection string sourced from application config.
    :rtype: str
    """

    return DB_CONFIG["database_url"]


def get_db_connection(database_url: str) -> psycopg.Connection:
    """Create a psycopg connection using the provided credentials.

    :param str database_url: Connection string targeting the reporting database.
    :return: Active psycopg connection instance.
    :rtype: psycopg.Connection
    """

    return connect(database_url=database_url)


def get_queries() -> QuestionAnswers:
    """Compute the formatted answers for each dashboard analysis question.

    :return: Mapping of formatted question labels to rendered answers.
    :rtype: QuestionAnswers
    """

    database_url = _database_url()
    connection = get_db_connection(database_url)

    with managed_connection(connection) as connection_ctx:
        with managed_cursor(connection_ctx) as cursor:
            results: QuestionAnswers = {}

            for question_idx, (question, query) in enumerate(QUESTION_QUERIES, start=1):
                label = f"{question_idx}. {question}"
                cursor.execute(query)
                rows = cursor.fetchall()

                if not rows or rows[0][0] is None:
                    results[label] = "No results found."
                    continue

                if len(rows) == 1 and len(rows[0]) == 1:
                    results[label] = f"{rows[0][0]}"
                    continue

                results[label] = "\n".join(
                    " | ".join(str(value) if value is not None else "NULL" for value in row)
                    for row in rows
                )

    _update_latest_analysis(results)
    return results


@app.route("/", methods=("GET", "POST"))
def index():
    """Render the dashboard, handling optional scrape or refresh postbacks.

    :return: Tuple pairing the rendered template and HTTP status code.
    :rtype: tuple[flask.wrappers.Response | str, int]
    """

    message = None
    question_answer: QuestionAnswers = {}
    status_code = 200
    database_url = _database_url()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "scrape":
            if is_scraping:
                message = "Scraping already in progress. Please wait."
                status_code = 409
                question_answer = dict(latest_analysis)
            else:
                _set_scraping(True)
                try:
                    main()
                    load_json_to_db(data_file, database_url)

                    with managed_connection(
                        get_db_connection(database_url)
                    ) as connection_ctx:
                        with managed_cursor(connection_ctx) as cursor:
                            cursor.execute(
                                """
                                SELECT COUNT(*) FROM applicants;
                                """
                            )
                            print("Total applicants in DB:", cursor.fetchone()[0])

                    question_answer = get_queries()
                    message = "Data pulled successfully!"
                finally:
                    _set_scraping(False)

        elif action == "refresh":
            if is_scraping:
                message = "Cannot update analysis: Pull Data is running."
                status_code = 409
                question_answer = dict(latest_analysis)
            else:
                question_answer = get_queries()
                message = "Analysis refreshed with latest database results."

    if not question_answer and status_code == 200:
        question_answer = latest_analysis or get_queries()

    return render_template("index.html", question_answer=question_answer, msg=message), status_code


if __name__ == "__main__":  # pragma: no cover - manual execution entry point
    app.run(host="0.0.0.0", port=8080, debug=True)
