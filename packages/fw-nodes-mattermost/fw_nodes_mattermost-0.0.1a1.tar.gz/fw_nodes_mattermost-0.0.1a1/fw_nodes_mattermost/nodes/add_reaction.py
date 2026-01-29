"""Mattermost Add Reaction node for adding emoji reactions to posts."""

from typing import Any

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


class MattermostAddReactionInput(BaseModel):
    """Input for adding a reaction to a Mattermost post."""

    credential_id: str = Field(
        ...,
        description="Mattermost credential with server URL and access token",
    )
    post_id: str = Field(
        ...,
        description="Post ID to add the reaction to",
    )
    emoji_name: str = Field(
        ...,
        description="Emoji name without colons (e.g., 'thumbsup', 'heart', 'smile')",
    )


class MattermostAddReactionOutput(BaseNodeOutput):
    """Output containing the created reaction data."""

    user_id: str = Field(..., description="User ID who added the reaction")
    post_id: str = Field(..., description="Post ID the reaction was added to")
    emoji_name: str = Field(..., description="Emoji name of the reaction")
    create_at: int = Field(..., description="Reaction creation timestamp (epoch ms)")
    success: bool = Field(..., description="Whether the reaction was added successfully")


class MattermostAddReactionNode(BaseNode):
    """Add an emoji reaction to a Mattermost post.

    This node uses the Mattermost REST API to add reactions to posts.
    Requires a Mattermost credential with server URL and access token.
    The emoji_name should be specified without colons (e.g., 'thumbsup' not ':thumbsup:').
    """

    input_schema = MattermostAddReactionInput
    output_schema = MattermostAddReactionOutput
    credential_schema = MattermostCredentialSchema

    metadata = NodeMetadata(
        name="Mattermost Add Reaction",
        description="Add an emoji reaction to a Mattermost post",
        category="mattermost",
        icon="👍",
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
    ) -> MattermostAddReactionOutput:
        """Add a reaction to a Mattermost post using the REST API."""
        credential_data = await context.resolve_credential(
            credential_id=validated_inputs["credential_id"],
            credential_type=self.get_credential_type(),
        )

        server_url = credential_data["server_url"].rstrip("/")
        access_token = credential_data["access_token"]

        context.register_secret(access_token)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            # Get current user ID (needed for reaction API)
            me_response = await client.get(
                f"{server_url}/api/v4/users/me",
                headers=headers,
                timeout=30,
            )

            if me_response.status_code >= 400:
                error_body = me_response.text
                try:
                    error_json = me_response.json()
                    error_message = error_json.get("message", error_body)
                except Exception:
                    error_message = error_body
                raise RuntimeError(f"Failed to get current user ({me_response.status_code}): {error_message}")

            user_id = me_response.json().get("id")

            # Add the reaction
            reaction_data = {
                "user_id": user_id,
                "post_id": validated_inputs["post_id"],
                "emoji_name": validated_inputs["emoji_name"],
            }

            response = await client.post(
                f"{server_url}/api/v4/reactions",
                headers=headers,
                json=reaction_data,
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

            return MattermostAddReactionOutput(
                user_id=result.get("user_id", ""),
                post_id=result.get("post_id", ""),
                emoji_name=result.get("emoji_name", ""),
                create_at=result.get("create_at", 0),
                success=True,
            )
