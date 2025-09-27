"""Form submission tests for scraping and refresh actions."""

import pytest


@pytest.mark.buttons
def test_post_pull_data_triggers_loader(app_env):
    """Assert POST scrape loads data once and persists inserts/commits via fake DB.

    :param tests.conftest.SimpleNamespace app_env: Flask test harness with client and mock DB.
    :return: ``None``
    :rtype: None
    """
    response = app_env.client.post("/", data={"action": "scrape"})

    assert response.status_code == 200
    assert len(app_env.db.inserted_rows) == len(app_env.sample_data)
    assert app_env.db.commit_calls == 1


@pytest.mark.buttons
def test_post_update_analysis_not_busy_returns_200(app_env):
    """Confirm refresh when idle hits the DB for analysis and returns 200.

    :param tests.conftest.SimpleNamespace app_env: Flask test harness with client and mock DB.
    :return: ``None``
    :rtype: None
    """
    response = app_env.client.post("/", data={"action": "refresh"})

    assert response.status_code == 200
    executed_queries = [sql for sql, _ in app_env.db.queries]
    assert any("SELECT COUNT(*) FROM applicants" in sql for sql in executed_queries)


@pytest.mark.buttons
def test_busy_refresh_returns_409_without_update(app_env):
    """Ensure refresh requests are rejected while scraping is flagged busy.

    :param tests.conftest.SimpleNamespace app_env: Flask test harness with client and mock DB.
    :return: ``None``
    :rtype: None
    """
    app_env.module.latest_analysis = {"cached": "value"}
    app_env.module.is_scraping = True
    before_queries = len(app_env.db.queries)

    response = app_env.client.post("/", data={"action": "refresh"})

    assert response.status_code == 409
    assert len(app_env.db.queries) == before_queries

    app_env.module.is_scraping = False


@pytest.mark.buttons
def test_busy_pull_returns_409(app_env):
    """Verify scrape requests return 409 when a pull is already in progress.

    :param tests.conftest.SimpleNamespace app_env: Flask test harness with client and mock DB.
    :return: ``None``
    :rtype: None
    """
    app_env.module.latest_analysis = {"cached": "value"}
    app_env.module.is_scraping = True
    before_inserts = len(app_env.db.inserted_rows)

    response = app_env.client.post("/", data={"action": "scrape"})

    assert response.status_code == 409
    assert len(app_env.db.inserted_rows) == before_inserts

    app_env.module.is_scraping = False
