"""End-to-end workflow tests covering scrape, refresh, and rendering."""

import pytest


@pytest.mark.integration
def test_end_to_end_pull_refresh_render(app_env):
    """Exercise pull then refresh to ensure DB rows exist and rendered HTML updates."""
    pull_response = app_env.client.post("/", data={"action": "scrape"})
    assert pull_response.status_code == 200
    assert len(app_env.db.inserted_rows) == len(app_env.sample_data)

    refresh_response = app_env.client.post("/", data={"action": "refresh"})
    assert refresh_response.status_code == 200

    page = app_env.client.get("/")
    html = page.data.decode("utf-8")

    assert page.status_code == 200
    assert "Example University" in html
    assert "Answer:" in html


@pytest.mark.integration
def test_multiple_pulls_preserve_uniqueness(app_env):
    """Confirm repeated pulls with identical data maintain one entry per URL."""
    first = app_env.client.post("/", data={"action": "scrape"})
    assert first.status_code == 200
    first_count = len(app_env.db.inserted_rows)

    second = app_env.client.post("/", data={"action": "scrape"})
    assert second.status_code == 200
    second_count = len(app_env.db.inserted_rows)

    assert first_count == second_count == len(app_env.sample_data)
