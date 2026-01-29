"""Tests for Return node."""

import pytest

from fw_nodes_core.nodes.return_node import ReturnNode

# node_execution_context fixture provided by conftest.py


@pytest.mark.asyncio
async def test_return_node_basic_key_value(node_execution_context):
    """Test Return node outputs key-value pairs."""
    node = ReturnNode()

    inputs = {
        "pairs": [
            {"key": "status", "value": "success"},
            {"key": "count", "value": 42},
        ]
    }

    result = await node.execute(inputs, node_execution_context)

    assert result.status == "success"
    assert result.count == 42


@pytest.mark.asyncio
async def test_return_node_duplicate_keys_error(node_execution_context):
    """Test Return node rejects duplicate keys."""
    node = ReturnNode()

    inputs = {
        "pairs": [
            {"key": "data", "value": "first"},
            {"key": "data", "value": "second"},
        ]
    }

    with pytest.raises(ValueError, match="Duplicate keys found: data"):
        await node.execute(inputs, node_execution_context)


@pytest.mark.asyncio
async def test_return_node_json_parsing(node_execution_context):
    """Test Return node parses JSON strings."""
    node = ReturnNode()

    inputs = {
        "pairs": [
            {"key": "obj", "value": '{"nested": "value"}'},
            {"key": "arr", "value": '[1, 2, 3]'},
        ]
    }

    result = await node.execute(inputs, node_execution_context)

    assert result.obj == {"nested": "value"}
    assert result.arr == [1, 2, 3]
