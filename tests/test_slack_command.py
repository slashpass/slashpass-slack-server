import sys
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

sys.modules["raven"] = MagicMock()
sys.modules["raven.contrib.flask"] = MagicMock()

from slack_command import view


@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(view, url_prefix="/api/slack_command")
    app.testing = True
    with app.test_client() as client:
        yield client


@patch("slack_command.db.session.query")
@patch("slack_command.valid_slack_request")
def test_api_help(valid_slack_request_mock, query_mock, client):
    valid_slack_request_mock.return_value = True

    mock_team = MagicMock()
    mock_team.team_id = "T12345"
    query_mock.return_value.filter_by.return_value.first.return_value = mock_team

    response = client.post(
        "/api/slack_command",
        data={
            "text": "help",
            "team_id": "T12345",
            "team_domain": "testdomain",
            "channel_id": "C12345",
        },
    )

    assert response.status_code == 200
    assert response.is_json
    json_data = response.get_json()
    assert "attachments" in json_data
    assert json_data["attachments"][0]["text"] == "*_Usage:_*"


@patch("slack_command.valid_slack_request")
def test_api_invalid_request(valid_slack_request_mock, client):
    valid_slack_request_mock.return_value = False

    response = client.post(
        "/api/slack_command",
        data={
            "text": "help",
            "team_id": "T12345",
            "team_domain": "testdomain",
            "channel_id": "C12345",
        },
    )

    assert response.status_code == 403


@patch("slack_command.db.session.query")
@patch("slack_command.valid_slack_request")
def test_api_no_team(valid_slack_request_mock, query_mock, client):
    valid_slack_request_mock.return_value = True

    query_mock.return_value.filter_by.return_value.first.return_value = None

    response = client.post(
        "/api/slack_command",
        data={
            "text": "help",
            "team_id": "T12345",
            "team_domain": "testdomain",
            "channel_id": "C12345",
        },
    )

    assert response.status_code == 200
    assert response.is_json
    json_data = response.get_json()
    assert (
        "You are not registered in our proxy server"
        in json_data["attachments"][0]["text"]
    )


@patch("slack_command.db.session.query")
@patch("slack_command.valid_slack_request")
@patch("slack_command.validators.url")
@patch("slack_command.Team.register_server")
def test_api_configure_new_server(
    register_server_mock, url_mock, valid_slack_request_mock, query_mock, client
):
    valid_slack_request_mock.return_value = True
    url_mock.return_value = True
    register_server_mock.return_value = True

    mock_team = MagicMock()
    mock_team.url = None
    query_mock.return_value.filter_by.return_value.first.return_value = mock_team

    response = client.post(
        "/api/slack_command",
        data={
            "text": "configure https://example.com",
            "team_id": "T12345",
            "team_domain": "testdomain",
            "channel_id": "C12345",
        },
    )

    assert response.status_code == 200
    assert response.is_json
    json_data = response.get_json()
    assert "successfully configured" in json_data["attachments"][0]["text"].lower()


@patch("slack_command.db.session.query")
@patch("slack_command.valid_slack_request")
@patch("slack_command.cmd.list")
def test_api_list_passwords(
    cmd_list_mock, valid_slack_request_mock, query_mock, client
):
    valid_slack_request_mock.return_value = True
    cmd_list_mock.return_value = "password1\npassword2"

    mock_team = MagicMock()
    query_mock.return_value.filter_by.return_value.first.return_value = mock_team

    response = client.post(
        "/api/slack_command",
        data={
            "text": "list",
            "team_id": "T12345",
            "team_domain": "testdomain",
            "channel_id": "C12345",
        },
    )

    assert response.status_code == 200
    assert response.is_json
    json_data = response.get_json()
    assert "password1" in json_data["attachments"][0]["text"]
    assert "password2" in json_data["attachments"][0]["text"]


@patch("slack_command.db.session.query")
@patch("slack_command.valid_slack_request")
@patch("slack_command.cmd.generate_insert_token")
def test_api_insert_secret(
    generate_insert_token_mock, valid_slack_request_mock, query_mock, client
):
    valid_slack_request_mock.return_value = True
    generate_insert_token_mock.return_value = "mock-token"

    mock_team = MagicMock()
    query_mock.return_value.filter_by.return_value.first.return_value = mock_team

    response = client.post(
        "/api/slack_command",
        data={
            "text": "insert mysecret",
            "team_id": "T12345",
            "team_domain": "testdomain",
            "channel_id": "C12345",
        },
    )

    assert response.status_code == 200
    assert response.is_json
    json_data = response.get_json()
    assert (
        "adding password for *mysecret*" in json_data["attachments"][0]["text"].lower()
    )
    assert "mock-token" in json_data["attachments"][0]["actions"][0]["url"]


@patch("slack_command.db.session.query")
@patch("slack_command.valid_slack_request")
@patch("slack_command.cmd.remove")
def test_api_remove_secret(
    cmd_remove_mock, valid_slack_request_mock, query_mock, client
):
    valid_slack_request_mock.return_value = True
    cmd_remove_mock.return_value = True

    mock_team = MagicMock()
    query_mock.return_value.filter_by.return_value.first.return_value = mock_team

    response = client.post(
        "/api/slack_command",
        data={
            "text": "remove mysecret",
            "team_id": "T12345",
            "team_domain": "testdomain",
            "channel_id": "C12345",
        },
    )

    assert response.status_code == 200
    assert response.is_json
    json_data = response.get_json()
    assert (
        "*mysecret* was removed successfully"
        in json_data["attachments"][0]["text"].lower()
    )


@patch("slack_command.db.session.query")
@patch("slack_command.valid_slack_request")
@patch("slack_command.cmd.show")
def test_api_show_secret(cmd_show_mock, valid_slack_request_mock, query_mock, client):
    valid_slack_request_mock.return_value = True
    cmd_show_mock.return_value = "https://example.com/mock-secret-link"

    mock_team = MagicMock()
    query_mock.return_value.filter_by.return_value.first.return_value = mock_team

    response = client.post(
        "/api/slack_command",
        data={
            "text": "show mysecret",
            "team_id": "T12345",
            "team_domain": "testdomain",
            "channel_id": "C12345",
        },
    )

    assert response.status_code == 200
    assert response.is_json
    json_data = response.get_json()
    assert "mock-secret-link" in json_data["attachments"][0]["actions"][0]["url"]
    assert "password for *mysecret*" in json_data["attachments"][0]["text"].lower()
