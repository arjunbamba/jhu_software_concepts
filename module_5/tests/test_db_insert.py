"""Behavioural tests for the database loader and query helpers."""

from __future__ import annotations

import json
from decimal import Decimal

import pytest

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

load_data = import_module("load_data")
course_app_module = import_module("homework_sample_code.course_app.app")

pytestmark = pytest.mark.db

DATABASE_URL = load_data.DEFAULT_DB_CONFIG["database_url"]


@pytest.mark.db
def test_load_json_to_db_inserts_rows(mock_db, sample_app_data, tmp_path):
    """Verify ``load_json_to_db`` inserts rows and records commits.

    :param MockDatabase mock_db: In-memory database double capturing inserts.
    :param list sample_app_data: Representative applicant payloads.
    :param pathlib.Path tmp_path: Temporary directory to host the JSON file.
    :return: ``None``
    :rtype: None
    """
    data_path = tmp_path / "applicants.json"
    data_path.write_text(json.dumps(sample_app_data))

    load_data.load_json_to_db(str(data_path), DATABASE_URL)

    assert len(mock_db.inserted_rows) == len(sample_app_data)
    first_row = mock_db.inserted_rows[0]
    assert first_row[0] == sample_app_data[0]["program"]
    assert first_row[7] == pytest.approx(3.8)
    assert first_row[8] == pytest.approx(322.0)
    assert mock_db.commit_calls == 1


@pytest.mark.db
def test_load_json_to_db_handles_empty_values(mock_db, tmp_path):
    """Ensure empty numeric fields remain ``NULL`` equivalents when loaded.

    :param MockDatabase mock_db: In-memory database capturing inserted rows.
    :param pathlib.Path tmp_path: Temporary directory used for JSON creation.
    :return: ``None``
    :rtype: None
    """
    data = [
        {
            "program": "Test Program",
            "comments": "",
            "date_added": "January 1, 2024",
            "url": "https://example.com",
            "status": "Pending",
            "term": "Fall 2025",
            "US/International": "American",
            "GPA": "",
            "GRE": "",
            "GRE V": "",
            "GRE AW": "",
            "Degree": "MS",
            "llm-generated-program": "",
            "llm-generated-university": "",
        }
    ]

    data_path = tmp_path / "applicants_empty.json"
    data_path.write_text(json.dumps(data))

    load_data.load_json_to_db(str(data_path), DATABASE_URL)

    assert len(mock_db.inserted_rows) == 1
    row = mock_db.inserted_rows[0]
    assert row[7] is None  # GPA
    assert row[8] is None  # GRE
    assert row[9] is None  # GRE V
    assert row[10] is None  # GRE AW


@pytest.mark.db
def test_get_queries_returns_expected_keys(mock_db):
    """Exercise ``get_queries`` to confirm the rendered response map.

    :param MockDatabase mock_db: Database double used to script query results.
    :return: ``None``
    :rtype: None
    """
    mock_db.reset()
    mock_db.set_script(
        {
            normalize_sql(QUERY_COUNT_FALL): [(3,)],
            normalize_sql(QUERY_PERCENT_INTERNATIONAL): [(Decimal("52.34"),)],
            normalize_sql(QUERY_AVG_SCORES): [
                (
                    Decimal("3.50"),
                    Decimal("320.00"),
                    Decimal("160.00"),
                    Decimal("4.00"),
                )
            ],
            normalize_sql(QUERY_AVG_AMERICAN): [(Decimal("3.40"),)],
            normalize_sql(QUERY_PERCENT_ACCEPT): [(Decimal("40.00"),)],
            normalize_sql(QUERY_AVG_ACCEPT_GPA): [(Decimal("3.60"),)],
            normalize_sql(QUERY_JHU_MS): [(4,)],
            normalize_sql(QUERY_GEORGETOWN_PHD): [(1,)],
            normalize_sql(QUERY_TOP_UNIVERSITY): [("Sample University", 9)],
            normalize_sql(QUERY_TOP_PROGRAM): [("Sample Program", 12)],
        }
    )

    result = course_app_module.get_queries()

    assert result["1. How many entries applied for Fall 2025?"] == "3"
    assert (
        result["2. Percentage of entries from international students (to 2 decimal places)"]
        == "52.34"
    )
    assert "Sample University" in result["9. Which university has the most applicants overall?"]
