"""Flask route integration coverage for the course app."""

import pytest


@pytest.mark.web
def test_app_factory_registers_routes(app_env):
    """Ensure the Flask app registers '/' with both GET and POST methods.

    :param tests.conftest.SimpleNamespace app_env: Flask test harness exposing app and client.
    :return: ``None``
    :rtype: None
    """
    app = app_env.module.app
    routes = {
        rule.rule: rule for rule in app.url_map.iter_rules() if rule.endpoint != "static"
    }

    assert "/" in routes
    methods = routes["/"].methods
    assert "GET" in methods
    assert "POST" in methods


@pytest.mark.web
def test_get_analysis_page_renders_expected_content(app_env):
    """Verify the analysis page renders the key buttons and analysis text.

    :param tests.conftest.SimpleNamespace app_env: Flask test harness exposing app and client.
    :return: ``None``
    :rtype: None
    """
    response = app_env.client.get("/")
    assert response.status_code == 200

    html = response.data.decode("utf-8")
    assert "Pull Data" in html
    assert "Update Analysis" in html
    assert "Analysis" in html
    assert "Answer:" in html
    assert "Example University" in html
