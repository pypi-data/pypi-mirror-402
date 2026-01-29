"""Tests for MattermostSlashCommandNode."""

import pytest

from fw_nodes_mattermost.nodes.slash_command import MattermostSlashCommandNode


@pytest.fixture
def slash_command_node():
    """Create a MattermostSlashCommandNode for testing."""
    return MattermostSlashCommandNode()


@pytest.fixture
def sample_slash_command_data():
    """Sample Mattermost slash command payload."""
    return {
        "token": "slash_token_456",
        "team_id": "team123",
        "team_domain": "myteam",
        "channel_id": "channel456",
        "channel_name": "general",
        "user_id": "user789",
        "user_name": "johndoe",
        "command": "/weather",
        "text": "San Francisco",
        "response_url": "https://mattermost.example.com/hooks/response123",
        "trigger_id": "trigger_abc",
    }


@pytest.mark.asyncio
async def test_slash_command_extracts_command_data(slash_command_node, mock_context, sample_slash_command_data):
    """Test that the node correctly extracts slash command data."""
    inputs = {
        "validate_token": False,
        "_trigger_data": {"body": sample_slash_command_data},
    }

    result = await slash_command_node.execute(inputs, mock_context)

    assert result.token == "slash_token_456"
    assert result.team_id == "team123"
    assert result.team_domain == "myteam"
    assert result.channel_id == "channel456"
    assert result.channel_name == "general"
    assert result.user_id == "user789"
    assert result.user_name == "johndoe"
    assert result.command == "/weather"
    assert result.text == "San Francisco"
    assert result.response_url == "https://mattermost.example.com/hooks/response123"
    assert result.trigger_id == "trigger_abc"


@pytest.mark.asyncio
async def test_slash_command_token_validation_success(slash_command_node, mock_context, sample_slash_command_data):
    """Test that token validation passes with correct token."""
    inputs = {
        "validate_token": True,
        "token": "slash_token_456",
        "_trigger_data": {"body": sample_slash_command_data},
    }

    result = await slash_command_node.execute(inputs, mock_context)

    assert result.command == "/weather"
    assert "slash_token_456" in mock_context.get_secrets()


@pytest.mark.asyncio
async def test_slash_command_token_validation_failure(slash_command_node, mock_context, sample_slash_command_data):
    """Test that token validation fails with incorrect token."""
    inputs = {
        "validate_token": True,
        "token": "wrong_token",
        "_trigger_data": {"body": sample_slash_command_data},
    }

    with pytest.raises(PermissionError, match="Invalid Mattermost slash command token"):
        await slash_command_node.execute(inputs, mock_context)


@pytest.mark.asyncio
async def test_slash_command_missing_token_in_request(slash_command_node, mock_context):
    """Test that validation fails when token is missing from request."""
    inputs = {
        "validate_token": True,
        "token": "expected_token",
        "_trigger_data": {"body": {"command": "/test"}},
    }

    with pytest.raises(PermissionError, match="Missing token"):
        await slash_command_node.execute(inputs, mock_context)


@pytest.mark.asyncio
async def test_slash_command_no_token_configured(slash_command_node, mock_context, sample_slash_command_data):
    """Test that validation fails when no token is configured but validation is enabled."""
    inputs = {
        "validate_token": True,
        "token": None,
        "_trigger_data": {"body": sample_slash_command_data},
    }

    with pytest.raises(PermissionError, match="no token is configured"):
        await slash_command_node.execute(inputs, mock_context)


@pytest.mark.asyncio
async def test_slash_command_rejects_empty_trigger_data(slash_command_node, mock_context):
    """Test that the node rejects missing or empty body."""
    inputs = {"validate_token": False}

    with pytest.raises(ValueError, match="missing or empty body"):
        await slash_command_node.execute(inputs, mock_context)
