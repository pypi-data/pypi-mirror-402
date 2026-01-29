"""Tests for WebhookResponseNode."""

import pytest

from fw_nodes_core.nodes.webhook_response import WebhookResponseNode


@pytest.fixture
def response_node():
    """Create a WebhookResponseNode instance."""
    return WebhookResponseNode()


# node_execution_context fixture provided by conftest.py


@pytest.mark.asyncio
async def test_response_default_values(response_node, node_execution_context):
    """Test that response node uses sensible defaults."""
    inputs = {}

    result = await response_node.execute(inputs, node_execution_context)

    assert result.status_code == 200
    assert result.body == ""
    assert result.content_type == "application/json"
    assert "Content-Type" in result.headers


@pytest.mark.asyncio
async def test_response_custom_status_code(response_node, node_execution_context):
    """Test setting a custom status code."""
    inputs = {
        "status_code": 201,
        "body": {"id": "123"},
    }

    result = await response_node.execute(inputs, node_execution_context)

    assert result.status_code == 201


@pytest.mark.asyncio
async def test_response_json_body_serialization(response_node, node_execution_context):
    """Test that dict body is serialized to JSON."""
    inputs = {
        "body": {"message": "success", "data": [1, 2, 3]},
        "content_type": "application/json",
    }

    result = await response_node.execute(inputs, node_execution_context)

    assert result.body == '{"message": "success", "data": [1, 2, 3]}'


@pytest.mark.asyncio
async def test_response_string_body_preserved(response_node, node_execution_context):
    """Test that string body is preserved as-is."""
    inputs = {
        "body": "Hello, World!",
        "content_type": "text/plain",
    }

    result = await response_node.execute(inputs, node_execution_context)

    assert result.body == "Hello, World!"


@pytest.mark.asyncio
async def test_response_custom_headers(response_node, node_execution_context):
    """Test setting custom response headers."""
    inputs = {
        "headers": {"X-Custom-Header": "custom-value"},
    }

    result = await response_node.execute(inputs, node_execution_context)

    assert result.headers["X-Custom-Header"] == "custom-value"
    assert result.headers["Content-Type"] == "application/json"


@pytest.mark.asyncio
async def test_response_none_body(response_node, node_execution_context):
    """Test that None body becomes empty string."""
    inputs = {
        "body": None,
    }

    result = await response_node.execute(inputs, node_execution_context)

    assert result.body == ""


@pytest.mark.asyncio
async def test_response_list_body(response_node, node_execution_context):
    """Test that list body is serialized to JSON."""
    inputs = {
        "body": [1, 2, 3],
        "content_type": "application/json",
    }

    result = await response_node.execute(inputs, node_execution_context)

    assert result.body == "[1, 2, 3]"


@pytest.mark.asyncio
async def test_response_is_terminal_node():
    """Test that response node is a terminal node (no outputs)."""
    node = WebhookResponseNode()
    metadata = node.get_metadata()

    assert metadata.handles.outputs == []


@pytest.mark.asyncio
async def test_response_has_input_handle():
    """Test that response node has one input handle."""
    node = WebhookResponseNode()
    metadata = node.get_metadata()

    assert len(metadata.handles.inputs) == 1
    assert metadata.handles.inputs[0].id == "default"


@pytest.mark.asyncio
async def test_response_error_status_codes(response_node, node_execution_context):
    """Test various error status codes."""
    for status_code in [400, 401, 403, 404, 500]:
        inputs = {
            "status_code": status_code,
            "body": {"error": "Something went wrong"},
        }

        result = await response_node.execute(inputs, node_execution_context)

        assert result.status_code == status_code


@pytest.mark.asyncio
async def test_response_html_content_type(response_node, node_execution_context):
    """Test HTML content type with string body."""
    inputs = {
        "body": "<html><body>Hello</body></html>",
        "content_type": "text/html",
    }

    result = await response_node.execute(inputs, node_execution_context)

    assert result.body == "<html><body>Hello</body></html>"
    assert result.content_type == "text/html"


@pytest.mark.asyncio
async def test_response_headers_converted_to_strings(response_node, node_execution_context):
    """Test that non-string header values are converted to strings."""
    inputs = {
        "headers": {
            "X-Count": 42,
            "X-Flag": True,
            "X-Name": "test",
        },
    }

    result = await response_node.execute(inputs, node_execution_context)

    # All header values should be strings
    assert result.headers["X-Count"] == "42"
    assert result.headers["X-Flag"] == "True"
    assert result.headers["X-Name"] == "test"
