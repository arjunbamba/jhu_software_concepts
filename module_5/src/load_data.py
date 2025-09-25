"""Utility helpers for provisioning and loading the applicants database."""

import json
from datetime import datetime, date
from pathlib import Path
from typing import Any, Mapping, Optional, Tuple, Union, cast

from psycopg import Connection, OperationalError, errors, sql
from psycopg.conninfo import conninfo_to_dict

from homework_sample_code.course_app.utils import (
    DEFAULT_DB_CONFIG,
    connect,
    make_admin_database_url,
    managed_connection,
    managed_cursor,
)


JsonPath = Union[str, Path]
APPLICANTS_TABLE = sql.Identifier("applicants")
DEFAULT_LIMIT = sql.Literal(10000)
INSERT_COLUMNS = [
    "program",
    "comments",
    "date_added",
    "url",
    "status",
    "term",
    "us_or_international",
    "gpa",
    "gre",
    "gre_v",
    "gre_aw",
    "degree",
    "llm_generated_program",
    "llm_generated_university",
]
INSERT_COLUMNS_SQL = sql.SQL(", ").join(sql.Identifier(name) for name in INSERT_COLUMNS)
PLACEHOLDERS_SQL = sql.SQL(", ").join(sql.Placeholder() for _ in INSERT_COLUMNS)
INSERT_APPLICANT = sql.SQL("INSERT INTO {table} ({columns}) VALUES ({values})").format(
    table=APPLICANTS_TABLE,
    columns=INSERT_COLUMNS_SQL,
    values=PLACEHOLDERS_SQL,
)
TRUNCATE_APPLICANTS = sql.SQL(
    "TRUNCATE TABLE {table} RESTART IDENTITY"
).format(table=APPLICANTS_TABLE)


def _commit_if_available(connection: Connection) -> None:
    """Commit the pending transaction when supported by the connection.

    :param Connection connection: Psycopg connection that may expose ``commit``.
    :return: ``None``
    :rtype: None
    """

    commit = getattr(connection, "commit", None)
    if callable(commit):
        commit()


def _parse_date(raw_date: Optional[str]) -> Optional[date]:
    """Convert GradCafe date strings into ``datetime.date`` instances.

    :param str raw_date: Date string in "Month DD, YYYY" form.
    :return: Parsed date object or ``None`` when parsing fails.
    :rtype: datetime.date | None
    """

    if not raw_date:
        return None

    try:
        return datetime.strptime(raw_date, "%B %d, %Y").date()
    except ValueError:
        return None


def _coerce_float(raw_value: Any) -> Optional[float]:
    """Safely convert user-supplied numeric strings to ``float`` values.

    :param Any raw_value: Input that may represent a numeric value.
    :return: Float representation or ``None`` when coercion is not possible.
    :rtype: float | None
    """

    if raw_value in (None, ""):
        return None

    try:
        return float(raw_value)
    except (TypeError, ValueError):
        return None


def _llm_text(raw_value: Optional[str]) -> str:
    """Normalise LLM-generated optional fields to non-null strings.

    :param str raw_value: Text provided by the LLM, possibly ``None``.
    :return: Original text or an empty string when the value is falsy.
    :rtype: str
    """

    return raw_value or ""


def _build_applicant_row(applicant: Mapping[str, Any]) -> Tuple[Any, ...]:
    """Prepare the parameter tuple for inserting an applicant record.

    :param Mapping applicant: Raw applicant dictionary sourced from JSON.
    :return: Tuple matching the insert statement column order.
    :rtype: tuple
    """

    return (
        applicant.get("program"),
        applicant.get("comments"),
        _parse_date(applicant.get("date_added")),
        applicant.get("url"),
        applicant.get("status"),
        applicant.get("term"),
        applicant.get("US/International"),
        _coerce_float(applicant.get("GPA")),
        _coerce_float(applicant.get("GRE")),
        _coerce_float(applicant.get("GRE V")),
        _coerce_float(applicant.get("GRE AW")),
        applicant.get("Degree"),
        _llm_text(applicant.get("llm-generated-program")),
        _llm_text(applicant.get("llm-generated-university")),
    )


# CONNECTION AND QUERY HELPERS
# ---------------------------------

def create_connection(database_url: str) -> Optional[Connection]:
    """Create a PostgreSQL connection using the supplied ``database_url``.

    :param str database_url: Psycopg connection string identifying the target database.
    :return: Live psycopg connection when successful; otherwise ``None``.
    :rtype: Connection | None
    """

    connection: Optional[Connection] = None
    try:
        connection = connect(database_url=database_url)
        print("Connection to PostgreSQL DB successful")
    except OperationalError as e:
        print(f"The error '{e}' occurred")
    return connection


def execute_query(connection: Optional[Connection], query: sql.Composable | str) -> None:
    """Execute a raw SQL statement on the provided connection.

    Autocommit mode is enabled prior to execution so DDL statements take effect
    immediately.

    :param Connection connection: Open database connection issuing the query.
    :param sql.Composable | str query: SQL to execute against the database.
    :return: ``None``
    :rtype: None
    """

    if connection is None:
        print("Cannot execute query without an active connection.")
        return

    connection.autocommit = True
    try:
        with managed_cursor(connection) as cursor:
            cursor.execute(query)
            print("Query executed successfully")
    except OperationalError as error:
        print(f"The error '{error}' occurred")


# SETUP DB + APPLICANTS TABLE
# ---------------------------------

def setup_database(database_url: str) -> None:
    """Provision the ``gradcafe`` database if it does not already exist.

    :param str database_url: Connection string targeting the ``gradcafe`` database.
    :return: ``None``
    :rtype: None
    """

    admin_url = make_admin_database_url(database_url)
    db_name = conninfo_to_dict(database_url).get("dbname", "gradcafe")

    raw_connection: Optional[Connection] = create_connection(admin_url)
    create_database_query = sql.SQL("CREATE DATABASE {db}").format(db=sql.Identifier(db_name))
    if raw_connection is None:
        return

    db_connection = cast(Connection, raw_connection)

    try:
        with managed_connection(db_connection) as connection_ctx:
            execute_query(connection_ctx, create_database_query)
    except errors.DuplicateDatabase as error:
        # Database probably exists already
        print(f"Skipping create database: {error}")


def setup_table(database_url: str) -> None:
    """Ensure the ``applicants`` table exists inside ``gradcafe``.

    :param str database_url: Connection string targeting the ``gradcafe`` database.
    :return: ``None``
    :rtype: None
    """

    raw_connection: Optional[Connection] = create_connection(database_url)

    if raw_connection is None:
        return

    db_connection = cast(Connection, raw_connection)

    create_applicants_table = sql.SQL(
        """
        CREATE TABLE IF NOT EXISTS {table} (
            p_id SERIAL PRIMARY KEY,
            program TEXT,
            comments TEXT,
            date_added DATE,
            url TEXT,
            status TEXT,
            term TEXT,
            us_or_international TEXT,
            gpa FLOAT,
            gre FLOAT,
            gre_v FLOAT,
            gre_aw FLOAT,
            degree TEXT,
            llm_generated_program TEXT,
            llm_generated_university TEXT
        );
        """
    ).format(table=APPLICANTS_TABLE)
    with managed_connection(db_connection) as connection_ctx:
        execute_query(connection_ctx, create_applicants_table)


# LOAD JSON DATA INTO APPLICANTS TABLE
# ------------------------------------------------

def load_json_to_db(json_path: JsonPath, database_url: str) -> None:
    """Load the cleaned applicant JSON document into the ``applicants`` table.

    The target table is truncated prior to inserting the refreshed dataset.

    :param str json_path: Filesystem path to the cleaned JSON payload.
    :param str database_url: Connection string targeting the ``gradcafe`` database.
    :return: ``None``
    :rtype: None
    """

    raw_connection: Optional[Connection] = create_connection(database_url)

    if raw_connection is None:
        return

    db_connection = cast(Connection, raw_connection)

    data_path = Path(json_path)

    with managed_connection(db_connection) as connection_ctx:
        with managed_cursor(connection_ctx) as cursor:
            cursor.execute(TRUNCATE_APPLICANTS)

            with data_path.open("r", encoding="utf-8") as json_file:
                for applicant in json.load(json_file):
                    cursor.execute(INSERT_APPLICANT, _build_applicant_row(applicant))

        _commit_if_available(connection_ctx)

    print("JSON data loaded from scratch into empty applicants table.")


def load_data() -> None:
    """Run the full data-loading pipeline for the admissions dataset.

    The helper creates the database and table if needed, refreshes the
    ``applicants`` table from ``llm_extend_applicant_data.json``, and prints a
    summary count of stored rows.

    :return: ``None``
    :rtype: None
    """
    db_config = DEFAULT_DB_CONFIG
    database_url = db_config["database_url"]

    setup_database(database_url)
    setup_table(database_url)

    # Load JSON data
    data_path = Path(__file__).resolve().parent / "llm_extend_applicant_data.json"
    if not data_path.exists():
        raise FileNotFoundError(f"Expected data file at {data_path}")

    load_json_to_db(str(data_path), database_url)

    raw_connection: Optional[Connection] = create_connection(database_url)
    if raw_connection is None:
        return

    db_connection = cast(Connection, raw_connection)

    with managed_connection(db_connection) as connection_ctx:
        with managed_cursor(connection_ctx) as cursor:
            # limited_subquery = sql.SQL(
            #     "SELECT 1 FROM {table} LIMIT {limit}"
            # ).format(table=APPLICANTS_TABLE, limit=DEFAULT_LIMIT)
            count_query = sql.SQL("SELECT COUNT(*) FROM {table}").format(
                table=APPLICANTS_TABLE
            )
            cursor.execute(count_query)
            print("Total applicants in DB:", cursor.fetchone()[0])


if __name__ == "__main__":
    load_data()
