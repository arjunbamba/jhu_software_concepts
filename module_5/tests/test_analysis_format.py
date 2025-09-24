import re

import pytest


@pytest.mark.analysis
def test_analysis_labels_present(app_env):
    """Check each rendered analysis block pairs Question and Answer labels."""
    response = app_env.client.get("/")
    html = response.data.decode("utf-8")

    assert response.status_code == 200
    assert html.count("Question:") == html.count("Answer:")


@pytest.mark.analysis
def test_percentage_values_render_with_two_decimals(app_env):
    """Ensure percentage answers display with two decimal places throughout the page."""
    app_env.client.post("/", data={"action": "scrape"})

    response = app_env.client.get("/")
    html = response.data.decode("utf-8")

    assert "66.67" in html
    assert not re.search(r"Answer:\s*\d+\.\d(?!\d)", html)
