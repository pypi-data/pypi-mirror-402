"""Tests for WebhookNode."""

import pytest

from fw_nodes_core.nodes.webhook import WebhookNode


@pytest.fixture
def webhook_node():
    """Create a WebhookNode instance."""
    return WebhookNode()


# node_execution_context fixture provided by conftest.py


@pytest.fixture
def sample_trigger_data():
    """Sample HTTP request trigger data."""
    return {
        "method": "POST",
        "path": "/webhook/abc-123",
        "query_params": {"foo": "bar"},
        "headers": {"content-type": "application/json", "x-api-key": "secret123"},
        "body": {"message": "hello"},
        "raw_body": '{"message": "hello"}',
        "content_type": "application/json",
    }


@pytest.mark.asyncio
async def test_webhook_outputs_request_data(webhook_node, node_execution_context, sample_trigger_data):
    """Test that webhook node outputs HTTP request data correctly."""
    inputs = {
        "auth_type": "none",
        "_trigger_data": sample_trigger_data,
    }

    result = await webhook_node.execute(inputs, node_execution_context)
    result_dict = result.model_dump(exclude_none=True, by_alias=True)

    assert result_dict["method"] == "POST"
    assert result_dict["path"] == "/webhook/abc-123"
    assert result_dict["query_params"] == {"foo": "bar"}
    assert result_dict["body"] == {"message": "hello"}
    assert result_dict["content_type"] == "application/json"


@pytest.mark.asyncio
async def test_webhook_no_auth_allows_all(webhook_node, node_execution_context, sample_trigger_data):
    """Test that auth_type='none' allows all requests."""
    inputs = {
        "auth_type": "none",
        "_trigger_data": sample_trigger_data,
    }

    # Should not raise
    result = await webhook_node.execute(inputs, node_execution_context)
    assert result.method == "POST"


@pytest.mark.asyncio
async def test_webhook_api_key_auth_valid(webhook_node, node_execution_context, sample_trigger_data):
    """Test that valid API key passes auth."""
    inputs = {
        "auth_type": "api_key",
        "api_key_header": "X-API-Key",
        "api_key": "secret123",
        "_trigger_data": sample_trigger_data,
    }

    # Should not raise - key matches
    result = await webhook_node.execute(inputs, node_execution_context)
    assert result.method == "POST"


@pytest.mark.asyncio
async def test_webhook_api_key_auth_invalid(webhook_node, node_execution_context, sample_trigger_data):
    """Test that invalid API key fails auth."""
    inputs = {
        "auth_type": "api_key",
        "api_key_header": "X-API-Key",
        "api_key": "wrong-key",
        "_trigger_data": sample_trigger_data,
    }

    with pytest.raises(PermissionError, match="Invalid API key"):
        await webhook_node.execute(inputs, node_execution_context)


@pytest.mark.asyncio
async def test_webhook_api_key_auth_missing_header(webhook_node, node_execution_context):
    """Test that missing API key header fails auth."""
    trigger_data = {
        "method": "POST",
        "path": "/webhook/abc-123",
        "headers": {},  # No API key header
        "body": None,
        "raw_body": "",
        "content_type": "",
        "query_params": {},
    }

    inputs = {
        "auth_type": "api_key",
        "api_key_header": "X-API-Key",
        "api_key": "secret123",
        "_trigger_data": trigger_data,
    }

    with pytest.raises(PermissionError, match="Missing API key"):
        await webhook_node.execute(inputs, node_execution_context)


@pytest.mark.asyncio
async def test_webhook_api_key_not_configured(webhook_node, node_execution_context, sample_trigger_data):
    """Test that api_key auth without configured key fails."""
    inputs = {
        "auth_type": "api_key",
        "api_key_header": "X-API-Key",
        "api_key": None,  # Not configured
        "_trigger_data": sample_trigger_data,
    }

    with pytest.raises(PermissionError, match="no API key is configured"):
        await webhook_node.execute(inputs, node_execution_context)


@pytest.mark.asyncio
async def test_webhook_empty_trigger_data(webhook_node, node_execution_context):
    """Test that empty trigger data uses defaults."""
    inputs = {
        "auth_type": "none",
        "_trigger_data": {},
    }

    result = await webhook_node.execute(inputs, node_execution_context)

    assert result.method == "POST"  # Default
    assert result.path == ""
    assert result.query_params == {}
    assert result.headers == {}
    assert result.body is None


@pytest.mark.asyncio
async def test_webhook_is_entry_point():
    """Test that webhook node is marked as entry point."""
    node = WebhookNode()
    metadata = node.get_metadata()

    assert metadata.is_entry_point is True
    assert metadata.show_execute_button is True


@pytest.mark.asyncio
async def test_webhook_has_no_input_handles():
    """Test that webhook node has no input handles."""
    node = WebhookNode()
    metadata = node.get_metadata()

    assert metadata.handles.inputs == []


@pytest.mark.asyncio
async def test_webhook_has_output_handle():
    """Test that webhook node has one output handle."""
    node = WebhookNode()
    metadata = node.get_metadata()

    assert len(metadata.handles.outputs) == 1
    assert metadata.handles.outputs[0].id == "default"


@pytest.mark.asyncio
async def test_webhook_api_key_header_case_insensitive(webhook_node, node_execution_context):
    """Test that API key header matching is case-insensitive."""
    trigger_data = {
        "method": "POST",
        "path": "/webhook/abc-123",
        "headers": {"X-Api-Key": "secret123"},  # Different case
        "body": None,
        "raw_body": "",
        "content_type": "",
        "query_params": {},
    }

    inputs = {
        "auth_type": "api_key",
        "api_key_header": "x-api-key",  # lowercase
        "api_key": "secret123",
        "_trigger_data": trigger_data,
    }

    # Should pass - header matching is case-insensitive
    result = await webhook_node.execute(inputs, node_execution_context)
    assert result.method == "POST"


@pytest.mark.asyncio
async def test_webhook_is_webhook_flag():
    """Test that webhook node has is_webhook=True metadata flag."""
    node = WebhookNode()
    metadata = node.get_metadata()

    assert metadata.is_webhook is True


@pytest.mark.asyncio
async def test_workflow_trigger_not_webhook():
    """Test that WorkflowTriggerNode does NOT have is_webhook=True."""
    from fw_nodes_core.nodes.trigger import WorkflowTriggerNode

    node = WorkflowTriggerNode()
    metadata = node.get_metadata()

    # WorkflowTriggerNode should NOT be triggerable via public webhook endpoint
    assert metadata.is_webhook is False
