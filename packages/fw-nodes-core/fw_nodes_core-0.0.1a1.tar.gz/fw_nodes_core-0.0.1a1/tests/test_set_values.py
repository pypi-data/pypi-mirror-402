"""Tests for Set Values node."""

import pytest

from fw_nodes_core.nodes.set_values import SetValuesNode, SetValuesOutput

# node_execution_context fixture provided by conftest.py


@pytest.mark.asyncio
async def test_basic_key_value_pairs(node_execution_context):
    """Test basic key-value pair output."""
    node = SetValuesNode()

    inputs = {
        "pairs": [
            {"key": "user_id", "value": "12345"},
            {"key": "status", "value": "active"},
        ]
    }

    result = await node.execute(inputs, node_execution_context)

    assert result.user_id == "12345"
    assert result.status == "active"


@pytest.mark.asyncio
async def test_json_object_parsing(node_execution_context):
    """Test that JSON objects are parsed correctly."""
    node = SetValuesNode()

    inputs = {
        "pairs": [
            {"key": "metadata", "value": '{"source": "api", "version": 2}'},
        ]
    }

    result = await node.execute(inputs, node_execution_context)

    assert isinstance(result.metadata, dict)
    assert result.metadata["source"] == "api"
    assert result.metadata["version"] == 2


@pytest.mark.asyncio
async def test_json_array_parsing(node_execution_context):
    """Test that JSON arrays are parsed correctly."""
    node = SetValuesNode()

    inputs = {
        "pairs": [
            {"key": "tags", "value": '["important", "verified"]'},
        ]
    }

    result = await node.execute(inputs, node_execution_context)

    assert isinstance(result.tags, list)
    assert result.tags == ["important", "verified"]


@pytest.mark.asyncio
async def test_invalid_json_fallback_to_string(node_execution_context):
    """Test that invalid JSON is kept as string."""
    node = SetValuesNode()

    inputs = {
        "pairs": [
            {"key": "data", "value": '{invalid}'},
        ]
    }

    result = await node.execute(inputs, node_execution_context)

    assert isinstance(result.data, str)
    assert result.data == '{invalid}'


@pytest.mark.asyncio
async def test_duplicate_keys_raises_error(node_execution_context):
    """Test that duplicate keys raise ValueError."""
    node = SetValuesNode()

    inputs = {
        "pairs": [
            {"key": "name", "value": "first"},
            {"key": "age", "value": "30"},
            {"key": "name", "value": "duplicate"},
        ]
    }

    with pytest.raises(ValueError) as exc_info:
        await node.execute(inputs, node_execution_context)

    assert "Duplicate keys found: name" in str(exc_info.value)
    assert "Each key must be unique" in str(exc_info.value)


@pytest.mark.asyncio
async def test_empty_pairs_returns_empty_object(node_execution_context):
    """Test that empty pairs list returns empty object."""
    node = SetValuesNode()

    inputs = {"pairs": []}

    result = await node.execute(inputs, node_execution_context)

    # Result should be valid SetValuesOutput with no extra fields
    assert isinstance(result, SetValuesOutput)
