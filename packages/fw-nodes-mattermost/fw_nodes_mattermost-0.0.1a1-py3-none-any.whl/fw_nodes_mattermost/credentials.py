"""Shared credential schemas for Mattermost nodes."""

from typing import ClassVar, Optional

from pydantic import BaseModel, Field


class MattermostCredentialSchema(BaseModel):
    """Credential schema for Mattermost API authentication.

    Shared across all Mattermost nodes in this package.
    """

    credential_name: ClassVar[str] = "Mattermost"
    credential_description: ClassVar[str] = "Mattermost server URL and access token"
    credential_icon: ClassVar[Optional[str]] = "💬"

    server_url: str = Field(
        ...,
        description="Mattermost server URL (e.g., https://mattermost.example.com)",
    )
    access_token: str = Field(
        ...,
        description="Personal access token or bot token",
    )
