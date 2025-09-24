import json
from types import SimpleNamespace

import pytest

import load_data


@pytest.mark.db
def test_create_connection_success(monkeypatch, capsys):
    """Ensure create_connection delegates to psycopg and returns the resulting connection."""

    class DummyConnection:
        pass

    captured_kwargs = {}

    def fake_connect(**kwargs):
        captured_kwargs.update(kwargs)
        return DummyConnection()

    monkeypatch.setattr(load_data.psycopg, "connect", fake_connect)

    conn = load_data.create_connection("gradcafe", "postgres", "abc123", "localhost", "5432")

    assert isinstance(conn, DummyConnection)
    assert captured_kwargs == {
        "dbname": "gradcafe",
        "user": "postgres",
        "password": "abc123",
        "host": "localhost",
        "port": "5432",
    }
    assert "Connection to PostgreSQL DB successful" in capsys.readouterr().out


@pytest.mark.db
def test_create_connection_handles_operational_error(monkeypatch, capsys):
    """Verify OperationalError is caught and None is returned while logging the error."""

    def fake_connect(**_kwargs):
        raise load_data.OperationalError("boom")

    monkeypatch.setattr(load_data.psycopg, "connect", fake_connect)

    conn = load_data.create_connection("gradcafe", "postgres", "abc123", "localhost", "5432")

    assert conn is None
    captured = capsys.readouterr().out
    assert "boom" in captured


@pytest.mark.db
def test_execute_query_executes_and_closes_cursor(capsys):
    """Ensure execute_query sets autocommit, executes SQL once, and closes the cursor."""

    class DummyCursor:
        def __init__(self):
            self.executed = []
            self.closed = False

        def execute(self, query):
            self.executed.append(query)

        def close(self):
            self.closed = True

    class DummyConnection:
        def __init__(self):
            self.autocommit = False
            self.cursor_obj = DummyCursor()

        def cursor(self):
            return self.cursor_obj

    conn = DummyConnection()

    load_data.execute_query(conn, "SELECT 1")

    assert conn.autocommit is True
    assert conn.cursor_obj.executed == ["SELECT 1"]
    assert conn.cursor_obj.closed is True
    assert "Query executed successfully" in capsys.readouterr().out


@pytest.mark.db
def test_setup_database_runs_create_query(monkeypatch):
    """setup_database should create a postgres connection, run CREATE DATABASE, and close it."""

    calls = SimpleNamespace(connect_args=None, executed_query=None, closed=False)

    class DummyConnection:
        def close(self):
            calls.closed = True

    def fake_create_connection(db_name, user, password, host, port):
        calls.connect_args = (db_name, user, password, host, port)
        return DummyConnection()

    def fake_execute(connection, query):
        calls.executed_query = query

    monkeypatch.setattr(load_data, "create_connection", fake_create_connection)
    monkeypatch.setattr(load_data, "execute_query", fake_execute)

    load_data.setup_database("postgres", "abc123", "localhost", "5432")

    assert calls.connect_args == ("postgres", "postgres", "abc123", "localhost", "5432")
    assert "CREATE DATABASE gradcafe" in calls.executed_query
    assert calls.closed is True


@pytest.mark.db
def test_setup_table_creates_applicants_table(monkeypatch):
    """setup_table should connect to gradcafe and issue the CREATE TABLE statement."""

    calls = SimpleNamespace(connect_args=None, executed_query=None, closed=False)

    class DummyConnection:
        def close(self):
            calls.closed = True

    def fake_create_connection(db_name, user, password, host, port):
        calls.connect_args = (db_name, user, password, host, port)
        return DummyConnection()

    def fake_execute(connection, query):
        calls.executed_query = query

    monkeypatch.setattr(load_data, "create_connection", fake_create_connection)
    monkeypatch.setattr(load_data, "execute_query", fake_execute)

    load_data.setup_table("postgres", "abc123", "localhost", "5432")

    assert calls.connect_args[0] == "gradcafe"
    assert "CREATE TABLE IF NOT EXISTS applicants" in calls.executed_query
    assert calls.closed is True


@pytest.mark.db
def test_load_data_orchestrates_pipeline(monkeypatch, capsys):
    """Run load_data with stubbed helpers to ensure orchestration and summary query execute."""

    call_order = []

    def fake_setup_database(*_args, **_kwargs):
        call_order.append("setup_database")

    def fake_setup_table(*_args, **_kwargs):
        call_order.append("setup_table")

    def fake_load_json(path, *_args):
        call_order.append(("load_json_to_db", path))

    class DummyCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, query):
            self.query = query

        def fetchone(self):
            return (7,)

    class DummyConnection:
        def __init__(self):
            self.closed = False

        def cursor(self):
            return DummyCursor()

        def close(self):
            self.closed = True

    connections = []

    def fake_create_connection(db_name, *_args, **_kwargs):
        connections.append(db_name)
        return DummyConnection()

    monkeypatch.setattr(load_data, "setup_database", fake_setup_database)
    monkeypatch.setattr(load_data, "setup_table", fake_setup_table)
    monkeypatch.setattr(load_data, "load_json_to_db", fake_load_json)
    monkeypatch.setattr(load_data, "create_connection", fake_create_connection)

    load_data.load_data()

    assert call_order[0] == "setup_database"
    assert call_order[1] == "setup_table"
    assert call_order[2][0] == "load_json_to_db"
    assert call_order[2][1].endswith("llm_extend_applicant_data.json")
    assert connections[-1] == "gradcafe"

    captured = capsys.readouterr().out
    assert "Total applicants in DB: 7" in captured
