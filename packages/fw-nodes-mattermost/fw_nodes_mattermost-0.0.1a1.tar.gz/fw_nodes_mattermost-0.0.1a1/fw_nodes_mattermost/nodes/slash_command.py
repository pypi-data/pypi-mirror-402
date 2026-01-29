"""Mattermost Slash Command node for receiving slash command invocations."""

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


class MattermostSlashCommandInput(BaseModel):
    """Configuration for the Mattermost slash command."""

    validate_token: bool = Field(
        default=False,
        description="Whether to validate the Mattermost slash command token",
    )
    token: Optional[str] = Field(
        default=None,
        description="Expected token from Mattermost (required if validate_token is True)",
    )


class MattermostSlashCommandOutput(BaseNodeOutput):
    """Output containing the Mattermost slash command data."""

    token: str = Field(..., description="The slash command token sent by Mattermost")
    team_id: str = Field(..., description="Team ID where the command was invoked")
    team_domain: str = Field(..., description="Team's domain name")
    channel_id: str = Field(..., description="Channel ID where the command was invoked")
    channel_name: str = Field(..., description="Channel's name")
    user_id: str = Field(..., description="User ID who invoked the command")
    user_name: str = Field(..., description="Username of the invoker")
    command: str = Field(..., description="The slash command itself (e.g., '/weather')")
    text: str = Field(..., description="Everything after the command (arguments)")
    response_url: str = Field(default="", description="URL to send delayed responses")
    trigger_id: str = Field(default="", description="ID for opening interactive dialogs")


class MattermostSlashCommandNode(BaseNode):
    """Mattermost slash command endpoint that triggers workflow execution.

    This node acts as an entry point for workflows triggered by Mattermost
    slash commands. When a user types a configured slash command (e.g., /mycommand),
    Mattermost sends the command data to this webhook.
    """

    input_schema = MattermostSlashCommandInput
    output_schema = MattermostSlashCommandOutput

    metadata = NodeMetadata(
        name="Mattermost Slash Command",
        description="Receive slash command invocations from Mattermost",
        category="mattermost",
        icon="⚡",
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
    ) -> MattermostSlashCommandOutput:
        """Validate token and return Mattermost slash command data."""
        # Parse expressions in schema fields
        inputs = await self.parse_expressions_in_schema_fields(inputs, context)

        # Get trigger data (HTTP request info from webhook endpoint)
        trigger_data = inputs.get("_trigger_data") or {}
        body = trigger_data.get("body")

        # Validate that we received a proper request body
        if not body or not isinstance(body, dict):
            error = "Invalid request: missing or empty body. Expected Mattermost slash command payload."
            context.publish_webhook_error(error, status_code=400)
            raise ValueError(error)

        # Validate token if configured
        if inputs.get("validate_token", False):
            await self._validate_token(inputs, body, context)

        # Extract Mattermost slash command fields from the POST body
        return MattermostSlashCommandOutput(
            token=body.get("token", ""),
            team_id=body.get("team_id", ""),
            team_domain=body.get("team_domain", ""),
            channel_id=body.get("channel_id", ""),
            channel_name=body.get("channel_name", ""),
            user_id=body.get("user_id", ""),
            user_name=body.get("user_name", ""),
            command=body.get("command", ""),
            text=body.get("text", ""),
            response_url=body.get("response_url", ""),
            trigger_id=body.get("trigger_id", ""),
        )

    async def _validate_token(
        self,
        inputs: dict[str, Any],
        body: dict[str, Any],
        context: NodeExecutionContext,
    ) -> None:
        """Validate the Mattermost slash command token.

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
            error = "Missing token in Mattermost slash command request"
            context.publish_webhook_error(error, status_code=401)
            raise PermissionError(error)

        if actual_token != expected_token:
            error = "Invalid Mattermost slash command token"
            context.publish_webhook_error(error, status_code=403)
            raise PermissionError(error)

        # Register the token as a secret so it's redacted from logs
        context.register_secret(expected_token)
