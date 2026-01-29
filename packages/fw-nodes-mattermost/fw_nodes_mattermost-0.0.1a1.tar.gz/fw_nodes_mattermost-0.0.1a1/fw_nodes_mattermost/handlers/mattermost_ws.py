"""Mattermost WebSocket stream handler."""

import json
import logging
from collections.abc import AsyncIterator
from typing import Any

import websockets
from flowire_sdk import StreamHandler
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)


class MattermostStreamHandler(StreamHandler):
    """Handler for Mattermost WebSocket connection.

    Connects to the Mattermost WebSocket API and streams real-time events
    like new messages, reactions, channel updates, etc.

    Stream type: mattermost_ws
    """

    STREAM_TYPE = "mattermost_ws"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ws = None
        self._seq = 1

    async def connect(self) -> None:
        """Establish WebSocket connection to Mattermost.

        1. Resolves credentials (server_url, access_token)
        2. Connects to WebSocket endpoint with Bearer token in header
        3. Verifies authentication via hello message
        """
        credential = await self.resolve_credential()

        # Get server URL and convert to WebSocket URL
        server_url = credential["server_url"].rstrip("/")
        ws_url = server_url.replace("https://", "wss://").replace("http://", "ws://")
        ws_url = f"{ws_url}/api/v4/websocket"

        logger.info(
            "Connecting to Mattermost WebSocket: %s subscription=%s",
            server_url,
            self.subscription.id,
        )

        # Build headers for authentication
        headers = {
            "Origin": server_url,
            "User-Agent": "Flowire-Connection-Manager/0.1.0",
            "Authorization": f"Bearer {credential['access_token']}",
        }

        # Connect to WebSocket with auth headers
        self.ws = await websockets.connect(
            ws_url,
            ping_interval=30,
            ping_timeout=10,
            additional_headers=headers,
            close_timeout=10,
        )

        # Wait for initial hello event
        hello_msg = await self.ws.recv()
        hello_data = json.loads(hello_msg)
        logger.debug("Received hello: %s", hello_data)

        # With Bearer token in header, authentication is immediate
        # The hello event's broadcast.user_id confirms we're authenticated
        broadcast = hello_data.get("broadcast", {})
        user_id = broadcast.get("user_id")

        if not user_id:
            raise RuntimeError("Mattermost authentication failed: no user_id in hello broadcast")

        logger.info(
            "Authenticated to Mattermost: user_id=%s subscription=%s",
            user_id,
            self.subscription.id,
        )

    async def disconnect(self) -> None:
        """Close WebSocket connection."""
        if self.ws:
            try:
                await self.ws.close()
            except Exception as e:
                logger.debug("Error closing WebSocket: %s", e)
            finally:
                self.ws = None

    async def listen(self) -> AsyncIterator[dict[str, Any]]:
        """Yield events from the Mattermost WebSocket.

        Filters to only yield actual events (not sequence replies or pings).
        """
        if not self.ws:
            raise RuntimeError("Not connected")

        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON from Mattermost: %s", message[:100])
                    continue

                # Skip sequence replies (responses to our requests)
                if "seq_reply" in data:
                    continue

                # Skip if no event type (not an event)
                if "event" not in data:
                    continue

                # Build event dict
                event = {
                    "event": data["event"],
                    "data": data.get("data", {}),
                    "broadcast": data.get("broadcast", {}),
                    "seq": data.get("seq"),
                }

                # Extract common fields for filtering
                broadcast = data.get("broadcast", {})
                event_data = data.get("data", {})

                # Add channel_id for filtering (from broadcast or data)
                if "channel_id" in broadcast:
                    event["channel_id"] = broadcast["channel_id"]
                elif "channel_id" in event_data:
                    event["channel_id"] = event_data["channel_id"]

                # Add team_id for filtering
                if "team_id" in broadcast:
                    event["team_id"] = broadcast["team_id"]
                elif "team_id" in event_data:
                    event["team_id"] = event_data["team_id"]

                # Add user_id for context
                if "user_id" in broadcast:
                    event["user_id"] = broadcast["user_id"]
                elif "user_id" in event_data:
                    event["user_id"] = event_data["user_id"]

                logger.debug(
                    "Mattermost event: type=%s channel=%s subscription=%s",
                    event["event"],
                    event.get("channel_id"),
                    self.subscription.id,
                )

                yield event

        except ConnectionClosed as e:
            logger.info(
                "Mattermost WebSocket closed: code=%s subscription=%s",
                e.code,
                self.subscription.id,
            )
            raise

    def should_forward(self, event: dict[str, Any]) -> bool:
        """Check if event matches subscription's filter.

        Extends base filtering with Mattermost-specific filters:
        - events: List of event types (e.g., ["posted", "reaction_added"])
        - channels: List of channel IDs to filter
        - teams: List of team IDs to filter
        """
        # First apply base filtering
        if not super().should_forward(event):
            return False

        event_filter = self.subscription.event_filter
        if not event_filter:
            return True

        # Team filter
        if "teams" in event_filter and event_filter["teams"]:
            team_id = event.get("team_id")
            if team_id and team_id not in event_filter["teams"]:
                return False

        return True
