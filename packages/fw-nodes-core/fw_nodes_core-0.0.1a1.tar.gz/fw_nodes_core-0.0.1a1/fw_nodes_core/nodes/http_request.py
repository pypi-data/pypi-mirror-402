"""HTTP Request node for making API calls."""

from enum import Enum
from typing import Any, ClassVar, Optional

import httpx
from flowire_sdk import BaseNode, BaseNodeOutput, NodeExecutionContext, NodeMetadata
from pydantic import BaseModel, Field


class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class HTTPBearerCredentialSchema(BaseModel):
    """Credential schema for HTTP Bearer token authentication."""

    # Class-level display metadata (optional)
    credential_name: ClassVar[str] = "HTTP Bearer Token"
    credential_description: ClassVar[str] = "Bearer token or API key for HTTP authentication"
    credential_icon: ClassVar[Optional[str]] = "🔑"

    # Instance fields (actual credential data)
    token: str = Field(..., description="Bearer token / API key")


class HTTPRequestInput(BaseModel):
    url: str = Field(..., description="The URL to request. Use Insert button to reference data from other nodes or project variables.")
    method: HTTPMethod = Field(default=HTTPMethod.GET, description="HTTP method")
    credential_id: Optional[str] = Field(None, description="Optional HTTP Bearer credential for authentication")
    headers: Optional[dict[str, str]] = Field(default=None, description="Request headers")
    params: Optional[dict[str, str]] = Field(default=None, description="Query parameters")
    body: Optional[dict[str, Any]] = Field(default=None, description="Request body (for POST/PUT/PATCH)")
    timeout: int = Field(default=30, description="Timeout in seconds")


class HTTPRequestOutput(BaseNodeOutput):
    body: Any = Field(..., description="Response body (parsed as JSON if possible)")
    status_code: int = Field(..., description="HTTP status code")
    headers: dict[str, str] = Field(..., description="Response headers")
    success: bool = Field(..., description="Whether request was successful (2xx status)")


class HTTPRequestNode(BaseNode):
    """Makes HTTP requests to external APIs."""

    # Schema definitions - no boilerplate methods needed!
    input_schema = HTTPRequestInput
    output_schema = HTTPRequestOutput
    credential_schema = HTTPBearerCredentialSchema

    metadata = NodeMetadata(
        name="HTTP Request",
        description="Make HTTP requests to external APIs",
        category="http",
        icon="🌐",
        color="#4CAF50",
    )

    async def execute_logic(
        self,
        validated_inputs: dict[str, Any],
        context: NodeExecutionContext,
    ) -> HTTPRequestOutput:
        """Execute HTTP request with pre-validated inputs."""
        # Resolve credential if provided (optional for HTTP requests)
        headers = validated_inputs.get("headers", {}) or {}
        if validated_inputs.get("credential_id"):
            credential_data = await context.resolve_credential(
                credential_id=validated_inputs["credential_id"],
                credential_type=self.get_credential_type()
            )
            # Add Bearer token to headers
            headers["Authorization"] = f"Bearer {credential_data['token']}"

        # Make HTTP request
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=validated_inputs["method"],
                url=validated_inputs["url"],
                headers=headers if headers else None,
                params=validated_inputs.get("params"),
                json=validated_inputs.get("body"),
                timeout=validated_inputs["timeout"],
            )

            # Try to parse as JSON, otherwise return text
            try:
                body = response.json()
            except Exception:
                body = response.text

            # Return Pydantic output instance (flat, no result wrapper)
            return HTTPRequestOutput(
                body=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                success=200 <= response.status_code < 300,
            )
