"""Tests for MattermostPostMessageNode."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from fw_nodes_mattermost.nodes.post_message import MattermostPostMessageNode


@pytest.fixture
def post_message_node():
    """Create a MattermostPostMessageNode for testing."""
    return MattermostPostMessageNode()


@pytest.fixture
def mock_context_with_credentials(mock_context):
    """Add Mattermost credentials to mock context."""
    mock_context._credentials = {
        "cred_mattermost_123": {
            "server_url": "https://mattermost.example.com",
            "access_token": "test_access_token_xyz",
        }
    }
    return mock_context


@pytest.fixture
def sample_mattermost_post_response():
    """Sample Mattermost API response for creating a post."""
    return {
        "id": "post_123abc",
        "channel_id": "channel_456",
        "message": "Hello from Flowire!",
        "create_at": 1640000000000,
        "user_id": "bot_user_789",
        "root_id": "",
        "type": "",
    }


@pytest.mark.asyncio
async def test_post_message_success(post_message_node, mock_context_with_credentials, sample_mattermost_post_response):
    """Test successful message posting to Mattermost."""
    inputs = {
        "credential_id": "cred_mattermost_123",
        "channel_id": "channel_456",
        "message": "Hello from Flowire!",
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample_mattermost_post_response

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        result = await post_message_node.execute(inputs, mock_context_with_credentials)

        assert result.post_id == "post_123abc"
        assert result.channel_id == "channel_456"
        assert result.message == "Hello from Flowire!"
        assert result.create_at == 1640000000000
        assert result.user_id == "bot_user_789"
        assert result.success is True

        # Verify the API was called correctly
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "https://mattermost.example.com/api/v4/posts"
        assert call_args[1]["headers"]["Authorization"] == "Bearer test_access_token_xyz"
        assert call_args[1]["json"]["channel_id"] == "channel_456"
        assert call_args[1]["json"]["message"] == "Hello from Flowire!"


@pytest.mark.asyncio
async def test_post_message_with_thread_reply(
    post_message_node, mock_context_with_credentials, sample_mattermost_post_response
):
    """Test posting a reply in a thread."""
    inputs = {
        "credential_id": "cred_mattermost_123",
        "channel_id": "channel_456",
        "message": "This is a reply!",
        "root_id": "parent_post_999",
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample_mattermost_post_response

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        await post_message_node.execute(inputs, mock_context_with_credentials)

        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["root_id"] == "parent_post_999"


@pytest.mark.asyncio
async def test_post_message_api_error(post_message_node, mock_context_with_credentials):
    """Test handling of Mattermost API error."""
    inputs = {
        "credential_id": "cred_mattermost_123",
        "channel_id": "invalid_channel",
        "message": "Hello!",
    }

    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = '{"message": "Channel not found"}'
    mock_response.json.return_value = {"message": "Channel not found"}

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        with pytest.raises(RuntimeError, match="Mattermost API error.*Channel not found"):
            await post_message_node.execute(inputs, mock_context_with_credentials)


@pytest.mark.asyncio
async def test_post_message_credential_not_found(post_message_node, mock_context):
    """Test error when credential is not found."""
    inputs = {
        "credential_id": "nonexistent_credential",
        "channel_id": "channel_456",
        "message": "Hello!",
    }

    with pytest.raises(ValueError, match="Credential nonexistent_credential not found"):
        await post_message_node.execute(inputs, mock_context)


@pytest.mark.asyncio
async def test_post_message_registers_token_as_secret(
    post_message_node, mock_context_with_credentials, sample_mattermost_post_response
):
    """Test that the access token is registered as a secret."""
    inputs = {
        "credential_id": "cred_mattermost_123",
        "channel_id": "channel_456",
        "message": "Hello!",
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample_mattermost_post_response

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        await post_message_node.execute(inputs, mock_context_with_credentials)

        assert "test_access_token_xyz" in mock_context_with_credentials.get_secrets()


@pytest.mark.asyncio
async def test_post_message_strips_trailing_slash_from_url(
    post_message_node, mock_context, sample_mattermost_post_response
):
    """Test that trailing slashes are stripped from server URL."""
    mock_context._credentials = {
        "cred_123": {
            "server_url": "https://mattermost.example.com/",  # Note trailing slash
            "access_token": "token",
        }
    }

    inputs = {
        "credential_id": "cred_123",
        "channel_id": "channel_456",
        "message": "Hello!",
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample_mattermost_post_response

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        await post_message_node.execute(inputs, mock_context)

        call_args = mock_client.post.call_args
        # Should not have double slash
        assert call_args[0][0] == "https://mattermost.example.com/api/v4/posts"
