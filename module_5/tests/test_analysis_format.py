"""HTML analysis formatting checks."""

import re

import pytest


@pytest.mark.analysis
def test_analysis_labels_present(app_env):
    """Check each rendered analysis block pairs Question and Answer labels.

    :param tests.conftest.SimpleNamespace app_env: Flask test harness with client and mock DB.
    :return: ``None``
    :rtype: None
    """
    response = app_env.client.get("/")
    html = response.data.decode("utf-8")

    assert response.status_code == 200
    assert html.count("Question:") == html.count("Answer:")


@pytest.mark.analysis
def test_percentage_values_render_with_two_decimals(app_env):
    """Ensure percentage answers display with two decimal places throughout the page.

    :param tests.conftest.SimpleNamespace app_env: Flask test harness with client and mock DB.
    :return: ``None``
    :rtype: None
    """
    app_env.client.post("/", data={"action": "scrape"})

    response = app_env.client.get("/")
    html = response.data.decode("utf-8")

    assert "66.67" in html
    assert not re.search(r"Answer:\s*\d+\.\d(?!\d)", html)
