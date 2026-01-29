"""Webhook Response node for sending HTTP responses back to webhook callers."""

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


class WebhookResponseInput(BaseModel):
    """Configuration for the webhook response."""

    status_code: int = Field(
        default=200,
        description="HTTP status code to return",
        ge=100,
        le=599,
    )
    body: Any = Field(
        default=None,
        description="Response body. Supports expressions like {{NodeId.field}}",
    )
    content_type: str = Field(
        default="application/json",
        description="Content-Type header for the response",
    )
    headers: Optional[dict[str, str]] = Field(
        default=None,
        description="Additional response headers",
    )


class WebhookResponseOutput(BaseNodeOutput):
    """Output confirming what was sent in the response."""

    status_code: int = Field(..., description="HTTP status code sent")
    body: Any = Field(default=None, description="Response body sent")
    content_type: str = Field(..., description="Content-Type header sent")
    headers: dict[str, str] = Field(default_factory=dict, description="Response headers sent")


class WebhookResponseNode(BaseNode):
    """Send HTTP response back to webhook caller.

    This is a terminal node (no output handles) that specifies what HTTP response
    to send back to the service that triggered the webhook.

    If multiple Webhook Response nodes exist in the workflow (e.g., in conditional
    branches), the first one to execute provides the response.

    If no Webhook Response node is reached, a default 200 OK response is returned.
    """

    input_schema = WebhookResponseInput
    output_schema = WebhookResponseOutput

    metadata = NodeMetadata(
        name="Webhook Response",
        description="Send HTTP response back to webhook caller",
        category="http",
        icon="📤",
        color="#4CAF50",
        handles=NodeHandles(
            inputs=[HandleConfig(id="default", position="left")],
            outputs=[],  # Terminal node - no outputs
        ),
        is_webhook_response=True,  # Tells executor to publish output as HTTP response
    )

    async def execute(
        self,
        inputs: dict[str, Any],
        context: NodeExecutionContext,
    ) -> WebhookResponseOutput:
        """Build and return the webhook response data.

        The workflow executor will detect this node's output and publish it
        via Redis pub/sub to the waiting webhook endpoint.
        """
        # Parse expressions in schema fields
        inputs = await self.parse_expressions_in_schema_fields(inputs, context)

        # Get response configuration
        status_code = inputs.get("status_code", 200)
        body = inputs.get("body")
        content_type = inputs.get("content_type", "application/json")
        headers = inputs.get("headers") or {}

        # Convert all header values to strings (HTTP headers are always strings)
        headers = {k: str(v) for k, v in headers.items()}

        # Serialize body to string if needed
        serialized_body = self._serialize_body(body, content_type)

        # Build response headers
        response_headers = {
            "Content-Type": content_type,
            **headers,
        }

        return WebhookResponseOutput(
            status_code=status_code,
            body=serialized_body,
            content_type=content_type,
            headers=response_headers,
        )

    def _serialize_body(self, body: Any, content_type: str) -> str:
        """Serialize the response body based on content type."""
        if body is None:
            return ""

        if isinstance(body, str):
            return body

        # For JSON content types, serialize dicts/lists
        if "json" in content_type.lower():
            if isinstance(body, (dict, list)):
                return json.dumps(body)
            return str(body)

        # For other content types, convert to string
        return str(body)
