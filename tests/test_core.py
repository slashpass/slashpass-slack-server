import pickle
from unittest.mock import MagicMock, patch

import pytest
from rsa import encrypt, generate_key

from core import SlashpassCMD, SlashpassError

secret_key = generate_key("test+key")

private_key = secret_key.exportKey("PEM")
public_key = secret_key.publickey().exportKey("PEM")


@pytest.fixture
def mock_cache():
    return MagicMock()


@pytest.fixture
def mock_team():
    class MockTeam:
        def __init__(self):
            self.id = "team123"

        def api(self, endpoint):
            return f"https://example.com/{endpoint}"

    return MockTeam()


@pytest.fixture
def slashpass(mock_cache):
    return SlashpassCMD(cache=mock_cache, private_key=private_key)


def test_list_success(slashpass, mock_team):
    channel = "test_channel"
    decrypted_data = f"{channel}/app1\n{channel}/app2"
    encrypted_data = encrypt(decrypted_data, public_key)

    with patch("requests.post") as mock_post:
        mock_post.return_value.text = encrypted_data
        mock_post.return_value.status_code = 200

        result = slashpass.list(mock_team, channel)

        assert "├─ app1" in result
        assert "└─ app2" in result
        mock_post.assert_called_once_with(mock_team.api(f"list/{channel}"))


def test_list_decryption_error(slashpass, mock_team):
    channel = "test_channel"

    # Mock the response from `requests.post`
    with patch("requests.post") as mock_post:
        mock_post.return_value.text = "invalid encrypted data"

        with pytest.raises(SlashpassError, match="Decryption error"):
            slashpass.list(mock_team, channel)


def test_generate_insert_token(slashpass, mock_cache, mock_team):
    channel = "test_channel"
    app = "test_app"

    token = slashpass.generate_insert_token(mock_team, channel, app)

    assert len(token) == 6
    assert token.isalnum()
    mock_cache.set.assert_called_once()


def test_insert_success(slashpass, mock_cache):
    token = "ABC123"
    secret = "supersecret"
    mock_cache.__getitem__.return_value = pickle.dumps(
        {"path": "test_channel/app", "url": "https://example.com/insert"}
    )

    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200

        slashpass.insert(token, secret)

        mock_post.assert_called_once_with(
            "https://example.com/insert",
            data={"path": "test_channel/app", "secret": secret},
        )
        mock_cache.delete.assert_called_once_with(token)


def test_insert_error(slashpass, mock_cache):
    token = "ABC123"
    secret = "supersecret"
    mock_cache.__getitem__.return_value = pickle.dumps(
        {"path": "test_channel/app", "url": "https://example.com/insert"}
    )

    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 500

        with pytest.raises(SlashpassError, match="Error 500"):
            slashpass.insert(token, secret)


def test_remove_success(slashpass, mock_team):
    channel = "test_channel"
    app = "test_app"

    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200

        result = slashpass.remove(mock_team, channel, app)

        assert result is True
        mock_post.assert_called_once_with(
            mock_team.api("remove"), data={"channel": channel, "app": app}
        )


def test_remove_failure(slashpass, mock_team):
    channel = "test_channel"
    app = "test_app"

    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 400

        result = slashpass.remove(mock_team, channel, app)

        assert result is False


def test_show_success(slashpass, mock_team):
    channel = "test_channel"
    app = "test_app"
    decrypted_data = "onetime link"
    encrypted_data = encrypt(decrypted_data, public_key)

    with patch("requests.post") as mock_post:
        mock_post.return_value.text = encrypted_data
        mock_post.return_value.status_code = 200

        result = slashpass.show(mock_team, channel, app)

        assert result == "onetime link"


def test_show_not_found(slashpass, mock_team):
    channel = "test_channel"
    app = "test_app"

    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 404

        result = slashpass.show(mock_team, channel, app)

        assert result is None


def test_show_unexpected_error(slashpass, mock_team):
    channel = "test_channel"
    app = "test_app"

    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 500

        with pytest.raises(SlashpassError, match="Unexpected error"):
            slashpass.show(mock_team, channel, app)
