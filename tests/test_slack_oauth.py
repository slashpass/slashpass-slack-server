import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

sys.modules["raven"] = MagicMock()
sys.modules["raven.contrib.flask"] = MagicMock()

from server import Team, db
from slack_oauth import view


@pytest.fixture
def app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"),
    )

    app.register_blueprint(view, url_prefix="/slack_oauth")
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///:memory:"  # Use an in-memory database for testing
    )
    db.init_app(app)

    with app.app_context():
        db.create_all()

    return app


@patch("requests.get")
def test_slack_oauth_success(mock_get, app):
    client = app.test_client()
    mock_response = {
        "ok": True,
        "access_token": "test_access_token",
        "authed_user": {"id": "U123456"},
        "bot_user_id": "B123456",
        "enterprise": {"id": "E123456", "name": "Enterprise Name"},
        "is_enterprise_install": True,
        "scope": "read write",
        "team": {"id": "T123456", "name": "Test Team"},
    }
    mock_get.return_value.json.return_value = mock_response

    response = client.get("/slack_oauth?code=valid_code")
    assert response.status_code == 200
    assert b'http-equiv="Refresh"' in response.data

    with app.app_context():
        team = Team.query.filter_by(team_id="T123456").first()
        assert team is not None
        assert team.team_name == "Test Team"


def test_slack_oauth_missing_code(app):
    client = app.test_client()
    response = client.get("/slack_oauth")
    assert response.status_code == 400


@patch("requests.get")
def test_slack_oauth_error(mock_get, app):
    client = app.test_client()
    mock_response = {"ok": False, "error": "invalid_code"}
    mock_get.return_value.json.return_value = mock_response

    response = client.get("/slack_oauth?code=invalid_code")
    assert response.status_code == 403


@patch("requests.get")
def test_slack_oauth_new_team(mock_get, app):
    client = app.test_client()
    mock_response = {
        "ok": True,
        "access_token": "test_access_token",
        "authed_user": {"id": "U123456"},
        "bot_user_id": "B123456",
        "enterprise": {"id": "E123456", "name": "Enterprise Name"},
        "is_enterprise_install": True,
        "scope": "read write",
        "team": {"id": "T123456", "name": "Test Team"},
    }
    mock_get.return_value.json.return_value = mock_response

    response = client.get("/slack_oauth?code=valid_code")
    assert response.status_code == 200
    with app.app_context():
        team = Team.query.filter_by(team_id="T123456").first()
        assert team is not None
        assert team.team_name == "Test Team"


@patch("requests.get")
def test_slack_oauth_no_enterprise(mock_get, app):
    client = app.test_client()
    mock_response = {
        "ok": True,
        "access_token": "test_access_token",
        "authed_user": {"id": "U123456"},
        "bot_user_id": "B123456",
        "enterprise": None,
        "is_enterprise_install": False,
        "scope": "read write",
        "team": {"id": "T123456", "name": "Test Team"},
    }
    mock_get.return_value.json.return_value = mock_response

    response = client.get("/slack_oauth?code=valid_code")
    assert response.status_code == 200
    with app.app_context():
        team = Team.query.filter_by(team_id="T123456").first()
        assert team is not None
        assert team.enterprise_id is None
