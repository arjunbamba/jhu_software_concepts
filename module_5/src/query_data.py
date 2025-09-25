"""Query helper utilities for the admissions analysis dataset."""

from typing import Tuple

from psycopg import sql

from homework_sample_code.course_app.utils import (
    DEFAULT_DB_CONFIG,
    connect,
    managed_connection,
    managed_cursor,
)

QuestionQuery = Tuple[str, sql.Composable]

APPLICANTS_TABLE = sql.Identifier("applicants")
TERM_COLUMN = sql.Identifier("term")
US_OR_INT_COLUMN = sql.Identifier("us_or_international")
STATUS_COLUMN = sql.Identifier("status")
DEGREE_COLUMN = sql.Identifier("degree")
UNIVERSITY_COLUMN = sql.Identifier("llm_generated_university")
PROGRAM_COLUMN = sql.Identifier("llm_generated_program")
GPA_COLUMN = sql.Identifier("gpa")
GRE_COLUMN = sql.Identifier("gre")
GRE_V_COLUMN = sql.Identifier("gre_v")
GRE_AW_COLUMN = sql.Identifier("gre_aw")

FALL_2025_LIKE = sql.Literal("%Fall 2025%")
INTERNATIONAL_LIKE = sql.Literal("%International%")
AMERICAN_LIKE = sql.Literal("%American%")
ACCEPT_LIKE = sql.Literal("%Accept%")
JHU_LIKE = sql.Literal("%Johns Hopkins%")
GEORGETOWN_LIKE = sql.Literal("%Georgetown%")
CS_LIKE = sql.Literal("%Computer Science%")
MASTER_LIKE = sql.Literal("%Master%")
PHD_LIKE = sql.Literal("%PhD%")
YEAR_2025_LIKE = sql.Literal("%2025%")
LIMIT_ONE = sql.Literal(1)


QUESTION_QUERIES: Tuple[QuestionQuery, ...] = (
    (
        "How many entries applied for Fall 2025?",
        sql.SQL(
            """
            SELECT COUNT(*)
            FROM {table}
            WHERE {term} ILIKE {fall_term}
            LIMIT {limit}
            """
        ).format(
            table=APPLICANTS_TABLE,
            term=TERM_COLUMN,
            fall_term=FALL_2025_LIKE,
            limit=LIMIT_ONE,
        ),
    ),
    (
        "Percentage of entries from international students (to 2 decimal places)",
        sql.SQL(
            """
            SELECT
                ROUND(
                    100.0 * COUNT(*) FILTER (WHERE {origin} ILIKE {intl})
                    / NULLIF(COUNT(*), 0),
                    2
                ) AS {alias}
            FROM {table}
            LIMIT {limit}
            """
        ).format(
            origin=US_OR_INT_COLUMN,
            intl=INTERNATIONAL_LIKE,
            alias=sql.Identifier("pct_international"),
            table=APPLICANTS_TABLE,
            limit=LIMIT_ONE,
        ),
    ),
    (
        "Average GPA, GRE, GRE V, GRE AW of applicants who provided them",
        sql.SQL(
            """
            SELECT
                ROUND(AVG({gpa})::numeric, 2) AS {avg_gpa},
                ROUND(AVG({gre})::numeric, 2) AS {avg_gre},
                ROUND(AVG({gre_v})::numeric, 2) AS {avg_gre_v},
                ROUND(AVG({gre_aw})::numeric, 2) AS {avg_gre_aw}
            FROM {table}
            LIMIT {limit}
            """
        ).format(
            gpa=GPA_COLUMN,
            avg_gpa=sql.Identifier("avg_gpa"),
            gre=GRE_COLUMN,
            avg_gre=sql.Identifier("avg_gre"),
            gre_v=GRE_V_COLUMN,
            avg_gre_v=sql.Identifier("avg_gre_v"),
            gre_aw=GRE_AW_COLUMN,
            avg_gre_aw=sql.Identifier("avg_gre_aw"),
            table=APPLICANTS_TABLE,
            limit=LIMIT_ONE,
        ),
    ),
    (
        "Average GPA of American students in Fall 2025",
        sql.SQL(
            """
            SELECT ROUND(AVG({gpa})::numeric, 2) AS {alias}
            FROM {table}
            WHERE {term} ILIKE {fall_term}
              AND {origin} ILIKE {american}
            LIMIT {limit}
            """
        ).format(
            gpa=GPA_COLUMN,
            alias=sql.Identifier("avg_gpa"),
            table=APPLICANTS_TABLE,
            term=TERM_COLUMN,
            fall_term=FALL_2025_LIKE,
            origin=US_OR_INT_COLUMN,
            american=AMERICAN_LIKE,
            limit=LIMIT_ONE,
        ),
    ),
    (
        "Percent of Fall 2025 entries that are Acceptances",
        sql.SQL(
            """
            SELECT ROUND(
                100.0 * COUNT(*) FILTER (WHERE {status} ILIKE {accept})
                / NULLIF(COUNT(*), 0),
                2
            ) AS {alias}
            FROM {table}
            WHERE {term} ILIKE {fall_term}
            LIMIT {limit}
            """
        ).format(
            status=STATUS_COLUMN,
            accept=ACCEPT_LIKE,
            alias=sql.Identifier("pct_acceptances"),
            table=APPLICANTS_TABLE,
            term=TERM_COLUMN,
            fall_term=FALL_2025_LIKE,
            limit=LIMIT_ONE,
        ),
    ),
    (
        "Average GPA of Fall 2025 Acceptances",
        sql.SQL(
            """
            SELECT ROUND(AVG({gpa})::numeric, 2) AS {alias}
            FROM {table}
            WHERE {term} ILIKE {fall_term}
              AND {status} ILIKE {accept}
            LIMIT {limit}
            """
        ).format(
            gpa=GPA_COLUMN,
            alias=sql.Identifier("avg_gpa"),
            table=APPLICANTS_TABLE,
            term=TERM_COLUMN,
            fall_term=FALL_2025_LIKE,
            status=STATUS_COLUMN,
            accept=ACCEPT_LIKE,
            limit=LIMIT_ONE,
        ),
    ),
    (
        "How many entries for JHU MS CS applicants",
        sql.SQL(
            """
            SELECT COUNT(*)
            FROM {table}
            WHERE {university} ILIKE {jhu}
              AND {program} ILIKE {cs}
              AND {degree} ILIKE {masters}
            LIMIT {limit}
            """
        ).format(
            table=APPLICANTS_TABLE,
            university=UNIVERSITY_COLUMN,
            jhu=JHU_LIKE,
            program=PROGRAM_COLUMN,
            cs=CS_LIKE,
            degree=DEGREE_COLUMN,
            masters=MASTER_LIKE,
            limit=LIMIT_ONE,
        ),
    ),
    (
        "How many 2025 PhD CS acceptances at Georgetown",
        sql.SQL(
            """
            SELECT COUNT(*)
            FROM {table}
            WHERE {university} ILIKE {georgetown}
              AND {program} ILIKE {cs}
              AND {degree} ILIKE {phd}
              AND {term} ILIKE {year_2025}
              AND {status} ILIKE {accept}
            LIMIT {limit}
            """
        ).format(
            table=APPLICANTS_TABLE,
            university=UNIVERSITY_COLUMN,
            georgetown=GEORGETOWN_LIKE,
            program=PROGRAM_COLUMN,
            cs=CS_LIKE,
            degree=DEGREE_COLUMN,
            phd=PHD_LIKE,
            term=TERM_COLUMN,
            year_2025=YEAR_2025_LIKE,
            status=STATUS_COLUMN,
            accept=ACCEPT_LIKE,
            limit=LIMIT_ONE,
        ),
    ),
    (
        "Which university has the most applicants overall?",
        sql.SQL(
            """
            SELECT {university}, COUNT(*) AS {alias}
            FROM {table}
            GROUP BY {university}
            ORDER BY {alias} DESC
            LIMIT {limit}
            """
        ).format(
            university=UNIVERSITY_COLUMN,
            alias=sql.Identifier("num_apps"),
            table=APPLICANTS_TABLE,
            limit=LIMIT_ONE,
        ),
    ),
    (
        "What is the most common program applicants apply to?",
        sql.SQL(
            """
            SELECT {program}, COUNT(*) AS {alias}
            FROM {table}
            GROUP BY {program}
            ORDER BY {alias} DESC
            LIMIT {limit}
            """
        ).format(
            program=PROGRAM_COLUMN,
            alias=sql.Identifier("num_apps"),
            table=APPLICANTS_TABLE,
            limit=LIMIT_ONE,
        ),
    ),
)


def run_queries(database_url: str) -> None:
    """Execute the canned analysis queries and print their results.

    :param str database_url: Connection string pointing to the reporting database.
    :return: ``None``
    :rtype: None
    """

    connection = connect(database_url=database_url)

    with managed_connection(connection) as connection_ctx:
        with managed_cursor(connection_ctx) as cursor:
            for index, (question, query) in enumerate(QUESTION_QUERIES, start=1):
                print(f"\n{index}. {question}")
                cursor.execute(query)

                rows = cursor.fetchall()
                if not rows or rows[0][0] is None:
                    print("   No results found.")

                if len(rows) == 1 and len(rows[0]) == 1:
                    print(f"   {rows[0][0]}")
                else:
                    for row in rows:
                        values = (
                            str(value) if value is not None else "NULL"
                            for value in row
                        )
                        print("   " + " | ".join(values))


if __name__ == "__main__":
    config = DEFAULT_DB_CONFIG
    run_queries(config["database_url"])
