import json
import sys
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

sys.modules["raven"] = MagicMock()
sys.modules["raven.contrib.flask"] = MagicMock()

from slack_action import view


@pytest.fixture
def client():
    """Fixture to set up a Flask test client."""
    app = Flask(__name__)
    app.register_blueprint(view, url_prefix="/slack")
    app.testing = True
    with app.test_client() as client:
        yield client


@patch("slack_action.valid_slack_request", return_value=True)
@patch("slack_action.db.session.query")
def test_no_actions(mock_query, mock_valid, client):
    """Test case for missing 'actions' in payload."""
    payload = {"callback_id": "configure_password_server"}
    response = client.post("/slack", data={"payload": json.dumps(payload)})
    assert response.status_code == 200
    assert response.data.decode() == "not implemented"


@patch("slack_action.valid_slack_request", return_value=False)
def test_invalid_request(mock_valid, client):
    """Test case for invalid Slack request."""
    payload = {}
    response = client.post("/slack", data={"payload": json.dumps(payload)})
    assert response.status_code == 404


@patch("slack_action.valid_slack_request", return_value=True)
def test_invalid_callback_id(mock_valid, client):
    """Test case for invalid callback_id."""
    payload = {"callback_id": "invalid_id", "actions": []}
    response = client.post("/slack", data={"payload": json.dumps(payload)})
    assert response.status_code == 200
    assert response.data.decode() == "not implemented"


@patch("slack_action.valid_slack_request", return_value=True)
@patch("slack_action.db.session.query")
def test_no_reconfigure(mock_query, mock_valid, client):
    """Test case for 'no_reconfigure' action."""
    payload = {
        "callback_id": "configure_password_server",
        "actions": [{"name": "no_reconfigure"}],
    }
    response = client.post("/slack", data={"payload": json.dumps(payload)})
    assert response.status_code == 200
    assert "Password server unchanged." in response.data.decode()


@patch("slack_action.valid_slack_request", return_value=True)
@patch("slack_action.db.session.query")
@patch("slack_action.validators.url", return_value=True)
def test_reconfigure_server_success(mock_valid_url, mock_query, mock_valid, client):
    """Test case for 'reconfigure_server' action with valid URL."""
    mock_team = MagicMock()
    mock_team.register_server.return_value = True
    mock_query.return_value.filter_by.return_value.first.return_value = mock_team

    payload = {
        "callback_id": "configure_password_server",
        "actions": [{"name": "reconfigure_server", "value": "https://example.com"}],
        "team": {"id": "team_id"},
    }
    response = client.post("/slack", data={"payload": json.dumps(payload)})
    assert response.status_code == 200
    assert "Password server successfully updated!" in response.data.decode()


@patch("slack_action.valid_slack_request", return_value=True)
@patch("slack_action.db.session.query")
def test_use_demo_server_failure(mock_query, mock_valid, client):
    """Test case for 'use_demo_server' action when registration fails."""
    mock_team = MagicMock()
    mock_team.register_server.return_value = False
    mock_query.return_value.filter_by.return_value.first.return_value = mock_team

    payload = {
        "callback_id": "configure_password_server",
        "actions": [{"name": "use_demo_server"}],
        "team": {"id": "team_id"},
    }
    response = client.post("/slack", data={"payload": json.dumps(payload)})
    assert response.status_code == 200
    assert "An error occurred registering the server" in response.data.decode()
