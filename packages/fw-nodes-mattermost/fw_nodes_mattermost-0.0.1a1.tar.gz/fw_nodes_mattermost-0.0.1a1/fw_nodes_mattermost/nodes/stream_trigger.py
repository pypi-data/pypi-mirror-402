"""Mattermost Stream Trigger node for receiving real-time WebSocket events."""

import json
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

from fw_nodes_mattermost.credentials import MattermostCredentialSchema


class MattermostStreamTriggerInput(BaseModel):
    """Configuration for Mattermost stream trigger."""

    credential_id: str = Field(
        ...,
        description="Mattermost credential with server URL and access token",
    )
    events: list[str] = Field(
        default=["posted", "reaction_added", "reaction_removed"],
        description="Event types to listen for (e.g., posted, reaction_added, reaction_removed, "
        "channel_created, user_added, typing, etc.)",
    )
    channels: Optional[list[str]] = Field(
        default=None,
        description="Channel IDs to filter events (null = all channels the user has access to)",
    )
    teams: Optional[list[str]] = Field(
        default=None,
        description="Team IDs to filter events (null = all teams)",
    )


class MattermostStreamTriggerOutput(BaseNodeOutput):
    """Output from Mattermost stream event."""

    event_type: str = Field(..., description="Event type (e.g., posted, reaction_added)")
    user_id: str = Field(default="", description="User who triggered the event")
    channel_id: str = Field(default="", description="Channel where event occurred")
    team_id: str = Field(default="", description="Team where event occurred")
    post_id: Optional[str] = Field(None, description="Post ID (for posted and reaction events)")
    message: Optional[str] = Field(None, description="Message content (for posted events)")
    emoji_name: Optional[str] = Field(None, description="Emoji name (for reaction events)")
    sender_name: Optional[str] = Field(None, description="Username of the sender")
    raw_event: dict = Field(default_factory=dict, description="Full event payload from Mattermost")


class MattermostStreamTriggerNode(BaseNode):
    """Trigger workflow on Mattermost events via WebSocket.

    This node receives real-time events from Mattermost through a persistent
    WebSocket connection maintained by the Connection Manager service.

    Unlike webhook-based triggers, this node:
    - Receives events in real-time (no polling delay)
    - Can capture events that webhooks can't (typing, status changes, etc.)
    - Doesn't require configuring webhooks in Mattermost admin

    The Connection Manager automatically establishes the WebSocket connection
    when a workflow containing this node is saved and enabled.
    """

    input_schema = MattermostStreamTriggerInput
    output_schema = MattermostStreamTriggerOutput
    credential_schema = MattermostCredentialSchema

    metadata = NodeMetadata(
        name="Mattermost Events",
        description="Trigger on real-time Mattermost events (messages, reactions, etc.) via WebSocket",
        category="mattermost",
        icon="📡",
        color="#0058CC",
        handles=NodeHandles(
            inputs=[],  # No inputs - entry point
            outputs=[HandleConfig(id="default", position="right")],
        ),
        is_entry_point=True,
        is_stream_trigger=True,
        stream_type="mattermost_ws",
        show_execute_button=True,
    )

    async def execute(
        self,
        inputs: dict[str, Any],
        context: NodeExecutionContext,
    ) -> MattermostStreamTriggerOutput:
        """Transform stream trigger data into structured output.

        When the Connection Manager receives a Mattermost event, it calls
        the internal trigger API which executes this node with the event
        data in _trigger_data.
        """
        # Parse expressions in schema fields
        inputs = await self.parse_expressions_in_schema_fields(inputs, context)

        # Get trigger data (event info from Connection Manager)
        trigger_data = inputs.get("_trigger_data") or {}

        # Extract event information
        event_type = trigger_data.get("event_type", "")
        event_data = trigger_data.get("event_data", {})
        broadcast = trigger_data.get("broadcast", {})

        # Extract common fields
        user_id = broadcast.get("user_id") or event_data.get("user_id", "")
        channel_id = broadcast.get("channel_id") or event_data.get("channel_id", "")
        team_id = broadcast.get("team_id") or event_data.get("team_id", "")

        # Extract event-specific fields
        post_id = None
        message = None
        emoji_name = None
        sender_name = None

        if event_type == "posted":
            # For posted events, the post data is in a JSON string
            post_str = event_data.get("post", "{}")
            if isinstance(post_str, str):
                try:
                    post = json.loads(post_str)
                except json.JSONDecodeError:
                    post = {}
            else:
                post = post_str or {}

            post_id = post.get("id")
            message = post.get("message")
            user_id = user_id or post.get("user_id", "")
            channel_id = channel_id or post.get("channel_id", "")

            sender_name = event_data.get("sender_name")

        elif event_type in ("reaction_added", "reaction_removed"):
            # Reaction events
            reaction = event_data.get("reaction", {})
            if isinstance(reaction, str):
                try:
                    reaction = json.loads(reaction)
                except json.JSONDecodeError:
                    reaction = {}

            post_id = reaction.get("post_id")
            emoji_name = reaction.get("emoji_name")
            user_id = user_id or reaction.get("user_id", "")

        # Parse JSON strings in event_data for cleaner raw_event
        def parse_json_strings(obj):
            """Recursively parse JSON strings in a dict or list."""
            if isinstance(obj, dict):
                return {k: parse_json_strings(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [parse_json_strings(item) for item in obj]
            elif isinstance(obj, str):
                stripped = obj.strip()
                if stripped.startswith(("{", "[")):
                    try:
                        return json.loads(stripped)
                    except json.JSONDecodeError:
                        return obj
            return obj

        parsed_event_data = parse_json_strings(event_data)

        # Build clean raw_event with parsed nested objects
        raw_event = {
            **trigger_data,
            "event_data": parsed_event_data,
        }

        return MattermostStreamTriggerOutput(
            event_type=event_type,
            user_id=user_id,
            channel_id=channel_id,
            team_id=team_id,
            post_id=post_id,
            message=message,
            emoji_name=emoji_name,
            sender_name=sender_name,
            raw_event=raw_event,
        )
