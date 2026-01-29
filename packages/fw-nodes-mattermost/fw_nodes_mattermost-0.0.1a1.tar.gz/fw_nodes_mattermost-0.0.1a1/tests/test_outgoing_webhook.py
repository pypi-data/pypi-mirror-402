"""Tests for MattermostOutgoingWebhookNode."""

import pytest

from fw_nodes_mattermost.nodes.outgoing_webhook import MattermostOutgoingWebhookNode


@pytest.fixture
def outgoing_webhook_node():
    """Create a MattermostOutgoingWebhookNode for testing."""
    return MattermostOutgoingWebhookNode()


@pytest.fixture
def sample_mattermost_webhook_data():
    """Sample Mattermost outgoing webhook payload."""
    return {
        "token": "test_token_123",
        "team_id": "team123",
        "team_domain": "myteam",
        "channel_id": "channel456",
        "channel_name": "general",
        "timestamp": "1640000000000",
        "user_id": "user789",
        "user_name": "johndoe",
        "post_id": "post_abc",
        "text": "Hello world!",
        "trigger_word": "hello",
        "file_ids": "",
    }


@pytest.mark.asyncio
async def test_outgoing_webhook_extracts_message_data(
    outgoing_webhook_node, mock_context, sample_mattermost_webhook_data
):
    """Test that the node correctly extracts Mattermost webhook data."""
    inputs = {
        "validate_token": False,
        "_trigger_data": {"body": sample_mattermost_webhook_data},
    }

    result = await outgoing_webhook_node.execute(inputs, mock_context)

    assert result.token == "test_token_123"
    assert result.team_id == "team123"
    assert result.team_domain == "myteam"
    assert result.channel_id == "channel456"
    assert result.channel_name == "general"
    assert result.timestamp == "1640000000000"
    assert result.user_id == "user789"
    assert result.user_name == "johndoe"
    assert result.post_id == "post_abc"
    assert result.text == "Hello world!"
    assert result.trigger_word == "hello"


@pytest.mark.asyncio
async def test_outgoing_webhook_token_validation_success(
    outgoing_webhook_node, mock_context, sample_mattermost_webhook_data
):
    """Test that token validation passes with correct token."""
    inputs = {
        "validate_token": True,
        "token": "test_token_123",
        "_trigger_data": {"body": sample_mattermost_webhook_data},
    }

    result = await outgoing_webhook_node.execute(inputs, mock_context)

    assert result.text == "Hello world!"
    assert "test_token_123" in mock_context.get_secrets()


@pytest.mark.asyncio
async def test_outgoing_webhook_token_validation_failure(
    outgoing_webhook_node, mock_context, sample_mattermost_webhook_data
):
    """Test that token validation fails with incorrect token."""
    inputs = {
        "validate_token": True,
        "token": "wrong_token",
        "_trigger_data": {"body": sample_mattermost_webhook_data},
    }

    with pytest.raises(PermissionError, match="Invalid Mattermost webhook token"):
        await outgoing_webhook_node.execute(inputs, mock_context)


@pytest.mark.asyncio
async def test_outgoing_webhook_missing_token_in_request(outgoing_webhook_node, mock_context):
    """Test that validation fails when token is missing from request."""
    inputs = {
        "validate_token": True,
        "token": "expected_token",
        "_trigger_data": {"body": {"text": "Hello"}},
    }

    with pytest.raises(PermissionError, match="Missing token"):
        await outgoing_webhook_node.execute(inputs, mock_context)


@pytest.mark.asyncio
async def test_outgoing_webhook_no_token_configured(
    outgoing_webhook_node, mock_context, sample_mattermost_webhook_data
):
    """Test that validation fails when no token is configured but validation is enabled."""
    inputs = {
        "validate_token": True,
        "token": None,
        "_trigger_data": {"body": sample_mattermost_webhook_data},
    }

    with pytest.raises(PermissionError, match="no token is configured"):
        await outgoing_webhook_node.execute(inputs, mock_context)


@pytest.mark.asyncio
async def test_outgoing_webhook_rejects_empty_trigger_data(outgoing_webhook_node, mock_context):
    """Test that the node rejects missing or empty body."""
    inputs = {"validate_token": False}

    with pytest.raises(ValueError, match="missing or empty body"):
        await outgoing_webhook_node.execute(inputs, mock_context)
