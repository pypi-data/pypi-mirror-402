"""Mattermost Outgoing Webhook node for receiving channel messages."""

from typing import Any, Optional

from flowire_sdk import (
    BaseNode,
    BaseNodeOutput,
    HandleConfig,
    NodeExecutionContext,
    NodeHandles,
    NodeMetadata,
)
from pydantic import BaseModel, Field


class MattermostOutgoingWebhookInput(BaseModel):
    """Configuration for the Mattermost outgoing webhook."""

    validate_token: bool = Field(
        default=False,
        description="Whether to validate the Mattermost webhook token",
    )
    token: Optional[str] = Field(
        default=None,
        description="Expected token from Mattermost (required if validate_token is True)",
    )


class MattermostOutgoingWebhookOutput(BaseNodeOutput):
    """Output containing the Mattermost outgoing webhook data."""

    token: str = Field(..., description="The webhook token sent by Mattermost")
    team_id: str = Field(..., description="Team ID where the message was posted")
    team_domain: str = Field(..., description="Team's domain name")
    channel_id: str = Field(..., description="Channel ID where the message was posted")
    channel_name: str = Field(..., description="Channel's name")
    timestamp: str = Field(..., description="Message timestamp (epoch milliseconds)")
    user_id: str = Field(..., description="User ID who posted the message")
    user_name: str = Field(..., description="Username of the poster")
    post_id: str = Field(..., description="Unique post ID")
    text: str = Field(..., description="The message content")
    trigger_word: str = Field(default="", description="The trigger word that activated the webhook (if configured)")
    file_ids: str = Field(default="", description="Comma-separated file IDs if attachments are present")


class MattermostOutgoingWebhookNode(BaseNode):
    """Mattermost outgoing webhook endpoint that triggers workflow execution.

    This node acts as an entry point for workflows triggered by Mattermost
    outgoing webhooks. When a message is posted in a configured channel or
    matches a trigger word, Mattermost sends the message data to this webhook.
    """

    input_schema = MattermostOutgoingWebhookInput
    output_schema = MattermostOutgoingWebhookOutput

    metadata = NodeMetadata(
        name="Mattermost Outgoing Webhook",
        description="Receive messages from Mattermost channels via outgoing webhooks",
        category="mattermost",
        icon="💬",
        color="#0058CC",
        handles=NodeHandles(
            inputs=[],  # No inputs - entry point
            outputs=[HandleConfig(id="default", position="right")],
        ),
        is_entry_point=True,
        is_webhook=True,
        show_execute_button=True,
    )

    async def execute(
        self,
        inputs: dict[str, Any],
        context: NodeExecutionContext,
    ) -> MattermostOutgoingWebhookOutput:
        """Validate token and return Mattermost webhook data."""
        # Parse expressions in schema fields
        inputs = await self.parse_expressions_in_schema_fields(inputs, context)

        # Get trigger data (HTTP request info from webhook endpoint)
        trigger_data = inputs.get("_trigger_data") or {}
        body = trigger_data.get("body")

        # Validate that we received a proper request body
        if not body or not isinstance(body, dict):
            error = "Invalid request: missing or empty body. Expected Mattermost webhook payload."
            context.publish_webhook_error(error, status_code=400)
            raise ValueError(error)

        # Validate token if configured
        if inputs.get("validate_token", False):
            await self._validate_token(inputs, body, context)

        # Send immediate 200 response to Mattermost so the connection doesn't hang
        # Mattermost outgoing webhooks don't use the response, so we acknowledge immediately
        context.publish_immediate_response(status_code=200, body="")

        # Extract Mattermost webhook fields from the POST body
        return MattermostOutgoingWebhookOutput(
            token=body.get("token", ""),
            team_id=body.get("team_id", ""),
            team_domain=body.get("team_domain", ""),
            channel_id=body.get("channel_id", ""),
            channel_name=body.get("channel_name", ""),
            timestamp=str(body.get("timestamp", "")),
            user_id=body.get("user_id", ""),
            user_name=body.get("user_name", ""),
            post_id=body.get("post_id", ""),
            text=body.get("text", ""),
            trigger_word=body.get("trigger_word", ""),
            file_ids=body.get("file_ids", ""),
        )

    async def _validate_token(
        self,
        inputs: dict[str, Any],
        body: dict[str, Any],
        context: NodeExecutionContext,
    ) -> None:
        """Validate the Mattermost webhook token.

        Raises:
            PermissionError: If token is missing or invalid
        """
        expected_token = inputs.get("token")

        if not expected_token:
            error = (
                "Token validation is enabled but no token is configured. "
                "Set the 'token' field in the node configuration."
            )
            context.publish_webhook_error(error, status_code=500)
            raise PermissionError(error)

        actual_token = body.get("token", "")

        if not actual_token:
            error = "Missing token in Mattermost webhook request"
            context.publish_webhook_error(error, status_code=401)
            raise PermissionError(error)

        if actual_token != expected_token:
            error = "Invalid Mattermost webhook token"
            context.publish_webhook_error(error, status_code=403)
            raise PermissionError(error)

        # Register the token as a secret so it's redacted from logs
        context.register_secret(expected_token)
