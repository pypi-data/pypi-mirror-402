"""Shared test fixtures for fw-nodes-mattermost tests."""

from typing import Any, Optional
from uuid import uuid4

import pytest
from flowire_sdk import NodeExecutionContext


class MockExecutionContext(NodeExecutionContext):
    """Mock execution context for testing nodes."""

    def __init__(
        self,
        workflow_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        node_id: Optional[str] = None,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
        node_results: Optional[dict[str, dict[str, Any]]] = None,
        project_variables: Optional[dict[str, Any]] = None,
        credentials: Optional[dict[str, dict]] = None,
    ):
        self.workflow_id = workflow_id or str(uuid4())
        self.execution_id = execution_id or str(uuid4())
        self.node_id = node_id or "test_node"
        self.project_id = project_id or str(uuid4())
        self.user_id = user_id or str(uuid4())
        self.node_results = node_results or {}
        self._secrets: set[str] = set()
        self._project_variables = project_variables or {}
        self._credentials = credentials or {}
        self._webhook_errors: list[tuple[str, int]] = []

    async def resolve_credential(self, credential_id: str, credential_type: str) -> dict:
        """Return mock credential or raise if not found."""
        if credential_id in self._credentials:
            return self._credentials[credential_id]
        raise ValueError(f"Credential {credential_id} not found")

    async def resolve_project_variable(self, key: str) -> Any:
        """Return mock project variable by key or raise if not found."""
        if key in self._project_variables:
            return self._project_variables[key]
        raise ValueError(f"Project variable {key} not found")

    async def resolve_project_variable_by_id(self, variable_id: str) -> Any:
        """Return mock project variable by ID or raise if not found."""
        if variable_id in self._project_variables:
            return self._project_variables[variable_id]
        raise ValueError(f"Project variable {variable_id} not found")

    def register_secret(self, value: str) -> None:
        """Register a secret value for redaction."""
        if value:
            self._secrets.add(value)

    def get_secrets(self) -> set:
        """Get registered secrets."""
        return self._secrets

    def publish_webhook_error(self, error: str, status_code: int = 400) -> None:
        """Record webhook error for testing."""
        self._webhook_errors.append((error, status_code))

    def publish_immediate_response(
        self,
        status_code: int = 200,
        body: Any = None,
        content_type: str = "application/json",
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        """Record immediate response for testing."""
        self._immediate_response = {
            "status_code": status_code,
            "body": body,
            "content_type": content_type,
            "headers": headers or {},
        }


@pytest.fixture
def mock_context():
    """Create a MockExecutionContext for testing."""
    return MockExecutionContext(
        workflow_id="wf_123",
        execution_id="exec_456",
        node_id="node_789",
        project_id="proj_abc",
        user_id="user_xyz",
        node_results={},
    )
