"""Tests for MattermostAddReactionNode."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from fw_nodes_mattermost.nodes.add_reaction import MattermostAddReactionNode


@pytest.fixture
def add_reaction_node():
    """Create a MattermostAddReactionNode for testing."""
    return MattermostAddReactionNode()


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
def sample_user_me_response():
    """Sample Mattermost API response for /users/me."""
    return {
        "id": "bot_user_789",
        "username": "flowire_bot",
        "email": "bot@example.com",
    }


@pytest.fixture
def sample_reaction_response():
    """Sample Mattermost API response for creating a reaction."""
    return {
        "user_id": "bot_user_789",
        "post_id": "post_123abc",
        "emoji_name": "thumbsup",
        "create_at": 1640000000000,
    }


@pytest.mark.asyncio
async def test_add_reaction_success(
    add_reaction_node,
    mock_context_with_credentials,
    sample_user_me_response,
    sample_reaction_response,
):
    """Test successful reaction addition to a Mattermost post."""
    inputs = {
        "credential_id": "cred_mattermost_123",
        "post_id": "post_123abc",
        "emoji_name": "thumbsup",
    }

    mock_me_response = MagicMock()
    mock_me_response.status_code = 200
    mock_me_response.json.return_value = sample_user_me_response

    mock_reaction_response = MagicMock()
    mock_reaction_response.status_code = 200
    mock_reaction_response.json.return_value = sample_reaction_response

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_me_response)
        mock_client.post = AsyncMock(return_value=mock_reaction_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        result = await add_reaction_node.execute(inputs, mock_context_with_credentials)

        assert result.user_id == "bot_user_789"
        assert result.post_id == "post_123abc"
        assert result.emoji_name == "thumbsup"
        assert result.create_at == 1640000000000
        assert result.success is True

        # Verify the /users/me API was called
        mock_client.get.assert_called_once()
        get_call_args = mock_client.get.call_args
        assert get_call_args[0][0] == "https://mattermost.example.com/api/v4/users/me"

        # Verify the /reactions API was called correctly
        mock_client.post.assert_called_once()
        post_call_args = mock_client.post.call_args
        assert post_call_args[0][0] == "https://mattermost.example.com/api/v4/reactions"
        assert post_call_args[1]["headers"]["Authorization"] == "Bearer test_access_token_xyz"
        assert post_call_args[1]["json"]["user_id"] == "bot_user_789"
        assert post_call_args[1]["json"]["post_id"] == "post_123abc"
        assert post_call_args[1]["json"]["emoji_name"] == "thumbsup"


@pytest.mark.asyncio
async def test_add_reaction_api_error(
    add_reaction_node,
    mock_context_with_credentials,
    sample_user_me_response,
):
    """Test handling of Mattermost API error when adding reaction."""
    inputs = {
        "credential_id": "cred_mattermost_123",
        "post_id": "invalid_post",
        "emoji_name": "thumbsup",
    }

    mock_me_response = MagicMock()
    mock_me_response.status_code = 200
    mock_me_response.json.return_value = sample_user_me_response

    mock_reaction_response = MagicMock()
    mock_reaction_response.status_code = 404
    mock_reaction_response.text = '{"message": "Post not found"}'
    mock_reaction_response.json.return_value = {"message": "Post not found"}

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_me_response)
        mock_client.post = AsyncMock(return_value=mock_reaction_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        with pytest.raises(RuntimeError, match="Mattermost API error.*Post not found"):
            await add_reaction_node.execute(inputs, mock_context_with_credentials)


@pytest.mark.asyncio
async def test_add_reaction_user_me_error(
    add_reaction_node,
    mock_context_with_credentials,
):
    """Test handling of error when fetching current user."""
    inputs = {
        "credential_id": "cred_mattermost_123",
        "post_id": "post_123abc",
        "emoji_name": "thumbsup",
    }

    mock_me_response = MagicMock()
    mock_me_response.status_code = 401
    mock_me_response.text = '{"message": "Invalid or expired token"}'
    mock_me_response.json.return_value = {"message": "Invalid or expired token"}

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_me_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        with pytest.raises(RuntimeError, match="Failed to get current user.*Invalid or expired token"):
            await add_reaction_node.execute(inputs, mock_context_with_credentials)


@pytest.mark.asyncio
async def test_add_reaction_credential_not_found(add_reaction_node, mock_context):
    """Test error when credential is not found."""
    inputs = {
        "credential_id": "nonexistent_credential",
        "post_id": "post_123abc",
        "emoji_name": "thumbsup",
    }

    with pytest.raises(ValueError, match="Credential nonexistent_credential not found"):
        await add_reaction_node.execute(inputs, mock_context)


@pytest.mark.asyncio
async def test_add_reaction_registers_token_as_secret(
    add_reaction_node,
    mock_context_with_credentials,
    sample_user_me_response,
    sample_reaction_response,
):
    """Test that the access token is registered as a secret."""
    inputs = {
        "credential_id": "cred_mattermost_123",
        "post_id": "post_123abc",
        "emoji_name": "heart",
    }

    mock_me_response = MagicMock()
    mock_me_response.status_code = 200
    mock_me_response.json.return_value = sample_user_me_response

    mock_reaction_response = MagicMock()
    mock_reaction_response.status_code = 200
    mock_reaction_response.json.return_value = sample_reaction_response

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_me_response)
        mock_client.post = AsyncMock(return_value=mock_reaction_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        await add_reaction_node.execute(inputs, mock_context_with_credentials)

        assert "test_access_token_xyz" in mock_context_with_credentials.get_secrets()


@pytest.mark.asyncio
async def test_add_reaction_strips_trailing_slash_from_url(
    add_reaction_node,
    mock_context,
    sample_user_me_response,
    sample_reaction_response,
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
        "post_id": "post_123abc",
        "emoji_name": "thumbsup",
    }

    mock_me_response = MagicMock()
    mock_me_response.status_code = 200
    mock_me_response.json.return_value = sample_user_me_response

    mock_reaction_response = MagicMock()
    mock_reaction_response.status_code = 200
    mock_reaction_response.json.return_value = sample_reaction_response

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_me_response)
        mock_client.post = AsyncMock(return_value=mock_reaction_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        await add_reaction_node.execute(inputs, mock_context)

        # Should not have double slash
        get_call_args = mock_client.get.call_args
        assert get_call_args[0][0] == "https://mattermost.example.com/api/v4/users/me"

        post_call_args = mock_client.post.call_args
        assert post_call_args[0][0] == "https://mattermost.example.com/api/v4/reactions"
