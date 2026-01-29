"""Webhook node for receiving external HTTP requests."""

from typing import Any, Literal, Optional

from flowire_sdk import (
    BaseNode,
    BaseNodeOutput,
    HandleConfig,
    NodeExecutionContext,
    NodeHandles,
    NodeMetadata,
)
from pydantic import BaseModel, Field


class WebhookInput(BaseModel):
    """Configuration for the webhook endpoint."""

    auth_type: Literal["none", "api_key"] = Field(
        default="none",
        description="Authentication type for this webhook",
    )
    api_key_header: str = Field(
        default="X-API-Key",
        description="Header name to check for API key (only used when auth_type is 'api_key')",
    )
    api_key: Optional[str] = Field(
        default=None,
        description="Expected API key value. Supports expressions like {{project.uuid}}",
    )


class WebhookOutput(BaseNodeOutput):
    """Output containing the incoming HTTP request data."""

    method: str = Field(..., description="HTTP method (GET, POST, PUT, DELETE, PATCH)")
    path: str = Field(..., description="Request path")
    query_params: dict[str, Any] = Field(
        default_factory=dict,
        description="URL query parameters",
    )
    headers: dict[str, str] = Field(
        default_factory=dict,
        description="Request headers",
    )
    body: Any = Field(default=None, description="Parsed request body (JSON if applicable)")
    raw_body: str = Field(default="", description="Raw request body as string")
    content_type: str = Field(default="", description="Content-Type header value")


class WebhookNode(BaseNode):
    """HTTP webhook endpoint that triggers workflow execution.

    This node acts as an entry point for workflows triggered by external HTTP requests.
    It receives the request data and makes it available to downstream nodes.

    Authentication is validated inside the node, allowing custom auth implementations
    in 3rd party webhook node types.
    """

    input_schema = WebhookInput
    output_schema = WebhookOutput

    metadata = NodeMetadata(
        name="Webhook",
        description="HTTP webhook endpoint that triggers workflow execution from external services",
        category="triggers",
        icon="🌐",
        color="#2196F3",
        handles=NodeHandles(
            inputs=[],  # No inputs - entry point
            outputs=[HandleConfig(id="default", position="right")],
        ),
        is_entry_point=True,
        is_webhook=True,  # Can be triggered via public /webhook/{id} endpoint
        show_execute_button=True,  # Allow manual execution for testing
    )

    async def execute(
        self,
        inputs: dict[str, Any],
        context: NodeExecutionContext,
    ) -> WebhookOutput:
        """Validate auth and return HTTP request data.

        The trigger data containing HTTP request info is automatically added to
        inputs._trigger_data by the workflow executor for entry point nodes.
        """
        # Parse expressions in schema fields (for api_key which may be {{project.uuid}})
        inputs = await self.parse_expressions_in_schema_fields(inputs, context)

        # Get trigger data (HTTP request info from webhook endpoint)
        trigger_data = inputs.get("_trigger_data", {})

        # Validate authentication if configured
        auth_type = inputs.get("auth_type", "none")
        if auth_type == "api_key":
            await self._validate_api_key_auth(inputs, trigger_data, context)

        # Extract request data from trigger_data
        method = trigger_data.get("method", "POST")
        path = trigger_data.get("path", "")
        query_params = trigger_data.get("query_params", {})
        headers = trigger_data.get("headers", {})
        body = trigger_data.get("body")
        raw_body = trigger_data.get("raw_body", "")
        content_type = trigger_data.get("content_type", "")

        return WebhookOutput(
            method=method,
            path=path,
            query_params=query_params,
            headers=headers,
            body=body,
            raw_body=raw_body,
            content_type=content_type,
        )

    async def _validate_api_key_auth(
        self,
        inputs: dict[str, Any],
        trigger_data: dict[str, Any],
        context: NodeExecutionContext,
    ) -> None:
        """Validate API key authentication.

        Raises:
            PermissionError: If API key is missing or invalid
        """
        expected_header = inputs.get("api_key_header", "X-API-Key")
        expected_key = inputs.get("api_key")

        if not expected_key:
            error = (
                "API key authentication is enabled but no API key is configured. "
                "Set the 'api_key' field in the webhook node configuration."
            )
            context.publish_webhook_error(error, status_code=500)
            raise PermissionError(error)

        # Get headers from trigger data (lowercase for case-insensitive comparison)
        headers = trigger_data.get("headers", {})
        headers_lower = {k.lower(): v for k, v in headers.items()}

        # Check for API key in headers
        actual_key = headers_lower.get(expected_header.lower())

        if not actual_key:
            error = f"Missing API key. Expected header: {expected_header}"
            context.publish_webhook_error(error, status_code=401)
            raise PermissionError(error)

        if actual_key != expected_key:
            error = "Invalid API key"
            context.publish_webhook_error(error, status_code=403)
            raise PermissionError(error)

        # Register the API key as a secret so it's redacted from logs
        context.register_secret(expected_key)
