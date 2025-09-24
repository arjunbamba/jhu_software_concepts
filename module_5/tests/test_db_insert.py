import json
from decimal import Decimal

import pytest

import textwrap

import load_data
from homework_sample_code.course_app import app as course_app_module


QUERY_PERCENT_INTERNATIONAL = textwrap.dedent(
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

QUERY_AVG_SCORES = textwrap.dedent(
    """
    SELECT
        ROUND(AVG(gpa)::numeric, 2) AS avg_gpa,
        ROUND(AVG(gre)::numeric, 2) AS avg_gre,
        ROUND(AVG(gre_v)::numeric, 2) AS avg_gre_v,
        ROUND(AVG(gre_aw)::numeric, 2) AS avg_gre_aw
    FROM applicants;
    """
)

QUERY_AVG_AMERICAN = textwrap.dedent(
    """
    SELECT ROUND(AVG(gpa)::numeric, 2) AS avg_gpa
    FROM applicants
    WHERE term ILIKE '%Fall 2025%'
      AND us_or_international ILIKE '%American%';
    """
)

QUERY_PERCENT_ACCEPT = textwrap.dedent(
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

QUERY_AVG_ACCEPT_GPA = textwrap.dedent(
    """
    SELECT ROUND(AVG(gpa)::numeric, 2) AS avg_gpa
    FROM applicants
    WHERE term ILIKE '%Fall 2025%'
      AND status ILIKE '%Accept%';
    """
)

QUERY_JHU_MS = textwrap.dedent(
    """
    SELECT COUNT(*)
    FROM applicants
    WHERE llm_generated_university ILIKE '%Johns Hopkins%'
      AND llm_generated_program ILIKE '%Computer Science%'
      AND degree ILIKE '%Master%';
    """
)

QUERY_GEORGETOWN_PHD = textwrap.dedent(
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

QUERY_TOP_UNIVERSITY = textwrap.dedent(
    """
    SELECT llm_generated_university, COUNT(*) AS num_apps
    FROM applicants
    GROUP BY llm_generated_university
    ORDER BY num_apps DESC
    LIMIT 1;
    """
)

QUERY_TOP_PROGRAM = textwrap.dedent(
    """
    SELECT llm_generated_program, COUNT(*) AS num_apps
    FROM applicants
    GROUP BY llm_generated_program
    ORDER BY num_apps DESC
    LIMIT 1;
    """
)

pytestmark = pytest.mark.db


@pytest.mark.db
def test_load_json_to_db_inserts_rows(mock_db, sample_app_data, tmp_path):
    """Run loader against sample JSON and confirm row insertion + commit bookkeeping."""
    data_path = tmp_path / "applicants.json"
    data_path.write_text(json.dumps(sample_app_data))

    load_data.load_json_to_db(
        str(data_path),
        db_user="postgres",
        db_password="abc123",
        db_host="localhost",
        db_port="5432",
    )

    assert len(mock_db.inserted_rows) == len(sample_app_data)
    first_row = mock_db.inserted_rows[0]
    assert first_row[0] == sample_app_data[0]["program"]
    assert first_row[7] == pytest.approx(3.8)
    assert first_row[8] == pytest.approx(322.0)
    assert mock_db.commit_calls == 1


@pytest.mark.db
def test_load_json_to_db_handles_empty_values(mock_db, tmp_path):
    """Verify empty numeric fields are preserved as NULL equivalents during load."""
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

    load_data.load_json_to_db(
        str(data_path),
        db_user="postgres",
        db_password="abc123",
        db_host="localhost",
        db_port="5432",
    )

    assert len(mock_db.inserted_rows) == 1
    row = mock_db.inserted_rows[0]
    assert row[7] is None  # GPA
    assert row[8] is None  # GRE
    assert row[9] is None  # GRE V
    assert row[10] is None  # GRE AW


@pytest.mark.db
def test_get_queries_returns_expected_keys(mock_db):
    """Stub query results and ensure question mapping returns expected formatted answers."""
    mock_db.reset()
    mock_db.set_script(
        {
            "SELECT COUNT(*) FROM applicants WHERE term ILIKE '%Fall 2025%';": [(3,)],
            QUERY_PERCENT_INTERNATIONAL: [(Decimal("52.34"),)],
            QUERY_AVG_SCORES: [
                (
                    Decimal("3.50"),
                    Decimal("320.00"),
                    Decimal("160.00"),
                    Decimal("4.00"),
                )
            ],
            QUERY_AVG_AMERICAN: [(Decimal("3.40"),)],
            QUERY_PERCENT_ACCEPT: [(Decimal("40.00"),)],
            QUERY_AVG_ACCEPT_GPA: [(Decimal("3.60"),)],
            QUERY_JHU_MS: [(4,)],
            QUERY_GEORGETOWN_PHD: [(1,)],
            QUERY_TOP_UNIVERSITY: [("Sample University", 9)],
            QUERY_TOP_PROGRAM: [("Sample Program", 12)],
        }
    )

    result = course_app_module.get_queries()

    assert result["1. How many entries applied for Fall 2025?"] == "3"
    assert result["2. Percentage of entries from international students (to 2 decimal places)"] == "52.34"
    assert "Sample University" in result["9. Which university has the most applicants overall?"]
