"""Tests for the query output helper module."""

from __future__ import annotations

import pytest

# pylint: disable=redefined-outer-name

from tests.conftest import normalize_sql
from tests.import_utils import import_module
from tests.query_constants import (
    QUERY_AVG_ACCEPT_GPA,
    QUERY_AVG_AMERICAN,
    QUERY_AVG_SCORES,
    QUERY_COUNT_FALL,
    QUERY_GEORGETOWN_PHD,
    QUERY_JHU_MS,
    QUERY_PERCENT_ACCEPT,
    QUERY_PERCENT_INTERNATIONAL,
    QUERY_TOP_PROGRAM,
    QUERY_TOP_UNIVERSITY,
)

query_data = import_module("query_data")
DATABASE_URL = query_data.DEFAULT_DB_CONFIG["database_url"]

QUERY1 = QUERY_COUNT_FALL
QUERY2 = QUERY_PERCENT_INTERNATIONAL
QUERY3 = QUERY_AVG_SCORES
QUERY4 = QUERY_AVG_AMERICAN
QUERY5 = QUERY_PERCENT_ACCEPT
QUERY6 = QUERY_AVG_ACCEPT_GPA
QUERY7 = QUERY_JHU_MS
QUERY8 = QUERY_GEORGETOWN_PHD
QUERY9 = QUERY_TOP_UNIVERSITY
QUERY10 = QUERY_TOP_PROGRAM


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

@pytest.fixture
def populated_query_db(query_db):
    """Provide a scripted database populated with deterministic query results.

    :param tests.conftest.MockDatabase query_db: Database double seeded by fixtures.
    :return: Database configured to return canned responses.
    :rtype: tests.conftest.MockDatabase
    """

    script = {
        normalize_sql(QUERY1): [(5,)],
        normalize_sql(QUERY2): [(47.50,)],
        normalize_sql(QUERY3): [(3.55, 321.0, 159.0, 4.2)],
        normalize_sql(QUERY4): [(3.60,)],
        normalize_sql(QUERY5): [(66.67,)],
        normalize_sql(QUERY6): [(3.75,)],
        normalize_sql(QUERY7): [(4,)],
        normalize_sql(QUERY8): [(2,)],
        normalize_sql(QUERY9): [("Top University", 23)],
        normalize_sql(QUERY10): [("Top Program", 41)],
    }
    query_db.set_script(script)
    return query_db


@pytest.mark.db
def test_run_queries_outputs_expected_values(populated_query_db, capsys):
    """Validate that ``run_queries`` prints the expected aggregated results.

    :param tests.conftest.MockDatabase populated_query_db: Database seeded with canned answers.
    :param _pytest.capture.CaptureFixture capsys: Pytest capture helper monitoring stdout.
    :return: ``None``
    :rtype: None
    """
    query_data.run_queries(DATABASE_URL)

    out = capsys.readouterr().out

    for question_index in range(1, 11):
        assert f"{question_index}." in out

    assert "Top University | 23" in out
    assert "Top Program | 41" in out
    assert "321.0 | 159.0 | 4.2" in out
    assert len(populated_query_db.queries) == len(ALL_QUERIES)


@pytest.fixture
def empty_result_query_db(query_db):
    """Provide a scripted database where every query yields an empty result set.

    :param tests.conftest.MockDatabase query_db: Database double reused across fixtures.
    :return: Database scripted to return empty lists for all queries.
    :rtype: tests.conftest.MockDatabase
    """

    script = {normalize_sql(query): [] for query in ALL_QUERIES}
    query_db.set_script(script)
    return query_db


@pytest.mark.db
def test_run_queries_handles_no_results(empty_result_query_db, capsys):
    """Ensure ``run_queries`` emits fallback output when datasets are empty.

    :param tests.conftest.MockDatabase empty_result_query_db: Database returning no rows.
    :param _pytest.capture.CaptureFixture capsys: Pytest capture helper monitoring stdout.
    :return: ``None``
    :rtype: None
    """
    query_data.run_queries(DATABASE_URL)

    out = capsys.readouterr().out

    # The helper should have printed the fallback line for each question
    assert out.count("No results found.") == len(ALL_QUERIES)
    assert len(empty_result_query_db.queries) == len(ALL_QUERIES)

    # ensure scalar formatting does not throw even on empty results
    normalized_queries = [normalize_sql(sql) for sql, _ in empty_result_query_db.queries]
    for query in ALL_QUERIES:
        assert normalize_sql(query) in normalized_queries
