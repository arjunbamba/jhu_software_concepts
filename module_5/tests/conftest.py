"""Shared pytest fixtures and helpers for the course app test suite."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from psycopg import sql

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

# pylint: disable=missing-class-docstring,missing-function-docstring,too-few-public-methods,redefined-outer-name

PROJECT_ROOT = Path(__file__).resolve().parents[1]


load_data = import_module("load_data")
course_app_module = import_module("homework_sample_code.course_app.app")


def normalize_sql(query) -> str:
    if isinstance(query, sql.Composable):
        rendered = query.as_string(None)
    else:
        rendered = str(query)
    cleaned = rendered.replace('"', "").strip()
    return " ".join(cleaned.split())


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


QUERY_COUNT_ALL = "SELECT COUNT(*) FROM applicants;"


def default_analysis_script(db: MockDatabase):
    return {
        normalize_sql(QUERY_COUNT_FALL): [(3,)],
        normalize_sql(QUERY_PERCENT_INTERNATIONAL): [(Decimal("47.50"),)],
        normalize_sql(QUERY_AVG_SCORES): [
            (
                Decimal("3.55"),
                Decimal("321.00"),
                Decimal("159.00"),
                Decimal("4.20"),
            )
        ],
        normalize_sql(QUERY_AVG_AMERICAN): [(Decimal("3.60"),)],
        normalize_sql(QUERY_PERCENT_ACCEPT): [(Decimal("66.67"),)],
        normalize_sql(QUERY_AVG_ACCEPT_GPA): [(Decimal("3.75"),)],
        normalize_sql(QUERY_JHU_MS): [(5,)],
        normalize_sql(QUERY_GEORGETOWN_PHD): [(2,)],
        normalize_sql(QUERY_TOP_UNIVERSITY): [("Example University", 12)],
        normalize_sql(QUERY_TOP_PROGRAM): [("Computer Science", 20)],
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

    query_module = import_module("query_data")

    def fake_connect(*_args, **_kwargs):
        return db.connect()

    monkeypatch.setattr(query_module, "connect", fake_connect)
    return db
