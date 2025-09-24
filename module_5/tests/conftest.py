import json
import sys
import textwrap
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

COURSE_APP_PATH = SRC_PATH / "homework_sample_code" / "course_app"
if str(COURSE_APP_PATH) not in sys.path:
    sys.path.insert(0, str(COURSE_APP_PATH))

import load_data
from homework_sample_code.course_app import app as course_app_module


def normalize_sql(query: str) -> str:
    return " ".join(query.strip().split())


class MockDatabase:
    def __init__(self):
        self.inserted_rows = []
        self.queries = []
        self.commit_calls = 0
        self.script = {}

    def connect(self):
        return MockConnection(self)

    def reset(self):
        self.inserted_rows = []
        self.queries = []
        self.commit_calls = 0

    def record_query(self, sql: str, params):
        self.queries.append((sql, params))

    def set_script(self, mapping):
        self.script = {normalize_sql(sql): value for sql, value in mapping.items()}


class MockConnection:
    def __init__(self, db: MockDatabase):
        self.db = db
        self.closed = False

    def cursor(self):
        return MockCursor(self)

    def commit(self):
        self.db.commit_calls += 1

    def close(self):
        self.closed = True


class MockCursor:
    def __init__(self, connection: MockConnection):
        self.connection = connection
        self.last_result = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, query, params=None):
        normalized = normalize_sql(query)
        self.connection.db.record_query(normalized, params)

        if "TRUNCATE TABLE applicants" in normalized:
            self.connection.db.inserted_rows = []

        if params is not None and "INSERT INTO applicants" in normalized:
            self.connection.db.inserted_rows.append(params)

        script = self.connection.db.script
        if normalized in script:
            result = script[normalized]
            if callable(result):
                result = result()
            self.last_result = result
        elif normalized == "SELECT COUNT(*) FROM applicants;":
            self.last_result = [(len(self.connection.db.inserted_rows),)]
        else:
            self.last_result = []

    def fetchall(self):
        return list(self.last_result)

    def fetchone(self):
        if self.last_result:
            return self.last_result[0]
        return (0,)

    def close(self):
        pass


QUERY_COUNT_FALL = textwrap.dedent(
    """
    SELECT COUNT(*)
    FROM applicants
    WHERE term ILIKE '%Fall 2025%';
    """
)

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

QUERY_COUNT_ALL = "SELECT COUNT(*) FROM applicants;"


def default_analysis_script(db: MockDatabase):
    return {
        QUERY_COUNT_FALL: [(3,)],
        QUERY_PERCENT_INTERNATIONAL: [(Decimal("47.50"),)],
        QUERY_AVG_SCORES: [(Decimal("3.55"), Decimal("321.00"), Decimal("159.00"), Decimal("4.20"))],
        QUERY_AVG_AMERICAN: [(Decimal("3.60"),)],
        QUERY_PERCENT_ACCEPT: [(Decimal("66.67"),)],
        QUERY_AVG_ACCEPT_GPA: [(Decimal("3.75"),)],
        QUERY_JHU_MS: [(5,)],
        QUERY_GEORGETOWN_PHD: [(2,)],
        QUERY_TOP_UNIVERSITY: [("Example University", 12)],
        QUERY_TOP_PROGRAM: [("Computer Science", 20)],
        QUERY_COUNT_ALL: lambda: [(len(db.inserted_rows),)],
    }


@pytest.fixture
def mock_db(monkeypatch):
    db = MockDatabase()

    def create_connection(*_args, **_kwargs):
        return db.connect()

    monkeypatch.setattr(load_data, "create_connection", create_connection)
    monkeypatch.setattr(course_app_module, "get_db_connection", create_connection)
    return db


@pytest.fixture
def sample_app_data():
    return [
        {
            "program": "Computer Science, MIT",
            "comments": "Accepted!",
            "date_added": "January 10, 2024",
            "url": "https://gradcafe.com/1",
            "status": "Accepted",
            "term": "Fall 2025",
            "US/International": "International",
            "GPA": "3.8",
            "GRE": "322",
            "GRE V": "160",
            "GRE AW": "4.5",
            "Degree": "MS",
            "llm-generated-program": "Computer Science",
            "llm-generated-university": "MIT",
        },
        {
            "program": "Physics, Stanford",
            "comments": "",
            "date_added": "February 1, 2024",
            "url": "https://gradcafe.com/2",
            "status": "Rejected",
            "term": "Fall 2025",
            "US/International": "American",
            "GPA": "3.6",
            "GRE": "",
            "GRE V": "155",
            "GRE AW": "",
            "Degree": "PhD",
            "llm-generated-program": "Physics",
            "llm-generated-university": "Stanford",
        },
    ]


@pytest.fixture
def app_env(mock_db, sample_app_data, monkeypatch, tmp_path):
    mock_db.reset()
    mock_db.set_script(default_analysis_script(mock_db))

    data_path = tmp_path / "applicants.json"
    data_path.write_text(json.dumps(sample_app_data))

    def fake_main():
        data_path.write_text(json.dumps(sample_app_data))

    monkeypatch.setattr(course_app_module, "data_file", str(data_path))
    monkeypatch.setattr(course_app_module, "main", fake_main)

    course_app_module.is_scraping = False
    course_app_module.latest_analysis = {}

    app = course_app_module.app
    previous_testing = app.config.get("TESTING")
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield SimpleNamespace(
            client=client,
            db=mock_db,
            module=course_app_module,
            sample_data=sample_app_data,
            data_path=str(data_path),
        )

    mock_db.reset()
    course_app_module.is_scraping = False
    course_app_module.latest_analysis = {}

    if previous_testing is None:
        app.config.pop("TESTING", None)
    else:
        app.config["TESTING"] = previous_testing


@pytest.fixture
def query_db(monkeypatch):
    db = MockDatabase()

    import query_data

    def fake_connect(*_args, **_kwargs):
        return db.connect()

    monkeypatch.setattr(query_data.psycopg, "connect", fake_connect)
    return db
