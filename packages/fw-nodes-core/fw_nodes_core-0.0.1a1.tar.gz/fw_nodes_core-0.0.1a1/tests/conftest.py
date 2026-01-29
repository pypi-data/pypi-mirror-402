"""Shared test fixtures for fw-nodes-core tests.

Provides a MockExecutionContext that implements the NodeExecutionContext
protocol for testing nodes without requiring the full flowire-app runtime.
"""

from typing import Any, Optional
from uuid import uuid4

import pytest
from flowire_sdk import NodeExecutionContext


class MockExecutionContext(NodeExecutionContext):
    """Mock execution context for testing nodes.

    This provides a minimal implementation of NodeExecutionContext
    that can be used to test nodes in isolation.
    """

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
        # For simplicity, treat ID same as key in mock
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


@pytest.fixture
def mock_context():
    """Create a MockExecutionContext for testing.

    Usage in tests:
        async def test_my_node(mock_context):
            node = MyNode()
            result = await node.execute(inputs, mock_context)

    Or create with custom data:
        def test_with_node_results(mock_context):
            mock_context.node_results = {"prev_node": {"value": 42}}
            ...
    """
    return MockExecutionContext()


@pytest.fixture
def mock_context_with_results():
    """Create a MockExecutionContext with sample node results.

    Useful for testing expression resolution.
    """
    return MockExecutionContext(
        node_results={
            "trigger_node": {
                "trigger_data": {"test_key": "test_value", "count": 42}
            },
            "http_node": {
                "body": {"title": "Test Title", "data": [1, 2, 3]},
                "status_code": 200,
                "success": True,
            },
        }
    )


@pytest.fixture
def mock_context_with_variables():
    """Create a MockExecutionContext with sample project variables.

    Useful for testing project variable resolution.
    """
    return MockExecutionContext(
        project_variables={
            "api_url": "https://api.example.com",
            "bucket_name": "test-bucket",
            "var-uuid-1": "resolved-value-1",
        }
    )


# Alias for backward compatibility with existing tests
@pytest.fixture
def node_execution_context():
    """Alias for mock_context - used by migrated tests.

    Most tests use this fixture name. It provides a MockExecutionContext
    with default values suitable for most node tests.
    """
    return MockExecutionContext(
        workflow_id="wf_123",
        execution_id="exec_456",
        node_id="node_789",
        project_id="proj_abc",
        user_id="user_xyz",
        node_results={},
    )
