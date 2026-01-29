"""Mattermost Post Message node for sending messages to Mattermost channels."""

from typing import Any, Optional

import httpx
from flowire_sdk import (
    BaseNode,
    BaseNodeOutput,
    HandleConfig,
    NodeExecutionContext,
    NodeHandles,
    NodeMetadata,
)
from pydantic import BaseModel, Field

from fw_nodes_mattermost.credentials import MattermostCredentialSchema


class MattermostPostMessageInput(BaseModel):
    """Input for posting a message to Mattermost."""

    credential_id: str = Field(
        ...,
        description="Mattermost credential with server URL and access token",
    )
    channel_id: str = Field(
        ...,
        description="Channel ID to post the message to",
    )
    message: str = Field(
        ...,
        description="Message content (supports Markdown)",
    )
    root_id: Optional[str] = Field(
        default=None,
        description="Post ID to reply to (creates a thread)",
    )
    props: Optional[dict[str, Any]] = Field(
        default=None,
        description="Additional post properties (e.g., attachments)",
    )


class MattermostPostMessageOutput(BaseNodeOutput):
    """Output containing the created post data."""

    post_id: str = Field(..., description="ID of the created post")
    channel_id: str = Field(..., description="Channel ID where post was created")
    message: str = Field(..., description="Message content")
    create_at: int = Field(..., description="Post creation timestamp (epoch ms)")
    user_id: str = Field(..., description="User ID who created the post")
    success: bool = Field(..., description="Whether the post was created successfully")


class MattermostPostMessageNode(BaseNode):
    """Post a message to a Mattermost channel.

    This node uses the Mattermost REST API to create posts in channels.
    Requires a Mattermost credential with server URL and access token.
    """

    input_schema = MattermostPostMessageInput
    output_schema = MattermostPostMessageOutput
    credential_schema = MattermostCredentialSchema

    metadata = NodeMetadata(
        name="Mattermost Post Message",
        description="Post a message to a Mattermost channel",
        category="mattermost",
        icon="📨",
        color="#0058CC",
        handles=NodeHandles(
            inputs=[HandleConfig(id="default", position="left")],
            outputs=[HandleConfig(id="default", position="right")],
        ),
    )

    async def execute_logic(
        self,
        validated_inputs: dict[str, Any],
        context: NodeExecutionContext,
    ) -> MattermostPostMessageOutput:
        """Post message to Mattermost using the REST API."""
        # Resolve Mattermost credential
        credential_data = await context.resolve_credential(
            credential_id=validated_inputs["credential_id"],
            credential_type=self.get_credential_type(),
        )

        server_url = credential_data["server_url"].rstrip("/")
        access_token = credential_data["access_token"]

        # Register token as secret so it's redacted from logs
        context.register_secret(access_token)

        # Build the post payload
        post_data: dict[str, Any] = {
            "channel_id": validated_inputs["channel_id"],
            "message": validated_inputs["message"],
        }

        if validated_inputs.get("root_id"):
            post_data["root_id"] = validated_inputs["root_id"]

        if validated_inputs.get("props"):
            post_data["props"] = validated_inputs["props"]

        # Make API request to create post
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{server_url}/api/v4/posts",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json=post_data,
                timeout=30,
            )

            if response.status_code >= 400:
                error_body = response.text
                try:
                    error_json = response.json()
                    error_message = error_json.get("message", error_body)
                except Exception:
                    error_message = error_body
                raise RuntimeError(f"Mattermost API error ({response.status_code}): {error_message}")

            result = response.json()

            return MattermostPostMessageOutput(
                post_id=result.get("id", ""),
                channel_id=result.get("channel_id", ""),
                message=result.get("message", ""),
                create_at=result.get("create_at", 0),
                user_id=result.get("user_id", ""),
                success=True,
            )
