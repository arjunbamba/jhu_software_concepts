import re
import textwrap

import pytest

import query_data

QUERY1 = textwrap.dedent(
    """
    SELECT COUNT(*)
    FROM applicants
    WHERE term ILIKE '%Fall 2025%';
    """
)

QUERY2 = textwrap.dedent(
    """
    SELECT
        ROUND(
            100.0 * COUNT(*) FILTER (WHERE us_or_international ILIKE '%International%')
            / NULLIF(COUNT(*), 0),
            2
        ) AS pct_international
    FROM applicants;
    """
)

QUERY3 = textwrap.dedent(
    """
    SELECT
        ROUND(AVG(gpa)::numeric, 2) AS avg_gpa,
        ROUND(AVG(gre)::numeric, 2) AS avg_gre,
        ROUND(AVG(gre_v)::numeric, 2) AS avg_gre_v,
        ROUND(AVG(gre_aw)::numeric, 2) AS avg_gre_aw
    FROM applicants;
    """
)

QUERY4 = textwrap.dedent(
    """
    SELECT ROUND(AVG(gpa)::numeric, 2) AS avg_gpa
    FROM applicants
    WHERE term ILIKE '%Fall 2025%'
      AND us_or_international ILIKE '%American%';
    """
)

QUERY5 = textwrap.dedent(
    """
    SELECT ROUND(
        100.0 * COUNT(*) FILTER (WHERE status ILIKE '%Accept%')
        / NULLIF(COUNT(*), 0),
        2
    ) AS pct_acceptances
    FROM applicants
    WHERE term ILIKE '%Fall 2025%';
    """
)

QUERY6 = textwrap.dedent(
    """
    SELECT ROUND(AVG(gpa)::numeric, 2) AS avg_gpa
    FROM applicants
    WHERE term ILIKE '%Fall 2025%'
      AND status ILIKE '%Accept%';
    """
)

QUERY7 = textwrap.dedent(
    """
    SELECT COUNT(*)
    FROM applicants
    WHERE llm_generated_university ILIKE '%Johns Hopkins%'
      AND llm_generated_program ILIKE '%Computer Science%'
      AND degree ILIKE '%Master%';
    """
)

QUERY8 = textwrap.dedent(
    """
    SELECT COUNT(*)
    FROM applicants
    WHERE llm_generated_university ILIKE '%Georgetown%'
      AND llm_generated_program ILIKE '%Computer Science%'
      AND degree ILIKE '%PhD%'
      AND term ILIKE '%2025%'
      AND status ILIKE '%Accept%';
    """
)

QUERY9 = textwrap.dedent(
    """
    SELECT llm_generated_university, COUNT(*) AS num_apps
    FROM applicants
    GROUP BY llm_generated_university
    ORDER BY num_apps DESC
    LIMIT 1;
    """
)

QUERY10 = textwrap.dedent(
    """
    SELECT llm_generated_program, COUNT(*) AS num_apps
    FROM applicants
    GROUP BY llm_generated_program
    ORDER BY num_apps DESC
    LIMIT 1;
    """
)


ALL_QUERIES = [
    QUERY1,
    QUERY2,
    QUERY3,
    QUERY4,
    QUERY5,
    QUERY6,
    QUERY7,
    QUERY8,
    QUERY9,
    QUERY10,
]


def normalize(sql: str) -> str:
    return " ".join(sql.strip().split())


@pytest.fixture
def populated_query_db(query_db):
    script = {
        QUERY1: [(5,)],
        QUERY2: [(47.50,)],
        QUERY3: [(3.55, 321.0, 159.0, 4.2)],
        QUERY4: [(3.60,)],
        QUERY5: [(66.67,)],
        QUERY6: [(3.75,)],
        QUERY7: [(4,)],
        QUERY8: [(2,)],
        QUERY9: [("Top University", 23)],
        QUERY10: [("Top Program", 41)],
    }
    query_db.set_script(script)
    return query_db


@pytest.mark.db
def test_run_queries_outputs_expected_values(populated_query_db, capsys):
    """Run run_queries against scripted results and assert printed content and query count."""
    query_data.run_queries("gradcafe", "postgres", "abc", "localhost", "5432")

    out = capsys.readouterr().out

    for question_index in range(1, 11):
        assert f"{question_index}." in out

    assert "Top University | 23" in out
    assert "Top Program | 41" in out
    assert "321.0 | 159.0 | 4.2" in out
    assert len(populated_query_db.queries) == len(ALL_QUERIES)


@pytest.fixture
def empty_result_query_db(query_db):
    script = {query: [] for query in ALL_QUERIES}
    query_db.set_script(script)
    return query_db


@pytest.mark.db
def test_run_queries_handles_no_results(empty_result_query_db, capsys):
    """Verify run_queries prints fallback text when every query returns no rows."""
    query_data.run_queries("gradcafe", "postgres", "abc", "localhost", "5432")

    out = capsys.readouterr().out

    # The helper should have printed the fallback line for each question
    assert out.count("No results found.") == len(ALL_QUERIES)
    assert len(empty_result_query_db.queries) == len(ALL_QUERIES)

    # ensure scalar formatting does not throw even on empty results
    for query in ALL_QUERIES:
        assert normalize(query) in [sql for sql, _ in empty_result_query_db.queries]
