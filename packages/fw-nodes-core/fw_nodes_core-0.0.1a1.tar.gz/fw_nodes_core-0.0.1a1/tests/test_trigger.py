"""Tests for WorkflowTriggerNode."""

import pytest

from fw_nodes_core.nodes.trigger import WorkflowTriggerNode


@pytest.fixture
def trigger_node():
    """Create a WorkflowTriggerNode instance."""
    return WorkflowTriggerNode()


# node_execution_context fixture provided by conftest.py


@pytest.mark.asyncio
async def test_trigger_data_in_output_field(trigger_node, node_execution_context):
    """Test that trigger_data is an actual output field containing trigger data."""
    # Arrange
    inputs = {"_trigger_data": {"webhook_id": "abc123", "payload": {"key": "value"}}}

    # Act
    result = await trigger_node.execute(inputs, node_execution_context)
    result = result.model_dump(exclude_none=True, by_alias=True)

    # Assert - trigger_data should be a field in output
    assert "trigger_data" in result
    assert result["trigger_data"]["webhook_id"] == "abc123"
    assert result["trigger_data"]["payload"]["key"] == "value"


@pytest.mark.asyncio
async def test_empty_trigger_data_outputs_none(trigger_node, node_execution_context):
    """Test that missing _trigger_data results in None in trigger_data field."""
    # Arrange
    inputs = {}

    # Act
    result = await trigger_node.execute(inputs, node_execution_context)
    result = result.model_dump(exclude_none=False, by_alias=True)

    # Assert - trigger_data should be None when not present
    assert "trigger_data" in result
    assert result["trigger_data"] is None


@pytest.mark.asyncio
async def test_no_initial_data_input(trigger_node):
    """Test that input schema does not have initial_data field."""
    # Get input schema
    input_schema = trigger_node.get_input_schema()

    # Assert - initial_data should not be in schema fields
    assert "initial_data" not in input_schema.model_fields


@pytest.mark.asyncio
async def test_trigger_data_in_output_schema(trigger_node):
    """Test that output schema includes trigger_data field."""
    # Get output schema
    output_schema = trigger_node.get_output_schema()

    # Assert - trigger_data should be in schema fields
    assert "trigger_data" in output_schema.model_fields


@pytest.mark.asyncio
async def test_string_trigger_data(trigger_node, node_execution_context):
    """Test that string trigger data (like HTML) is preserved as-is."""
    # Arrange
    html_string = '<div role="listitem">Some content</div>'
    inputs = {"_trigger_data": html_string}

    # Act
    result = await trigger_node.execute(inputs, node_execution_context)
    result = result.model_dump(exclude_none=True, by_alias=True)

    # Assert - string data should be preserved
    assert "trigger_data" in result
    assert result["trigger_data"] == html_string


@pytest.mark.asyncio
async def test_list_trigger_data(trigger_node, node_execution_context):
    """Test that list trigger data is preserved as-is."""
    # Arrange
    list_data = [1, 2, 3, "test"]
    inputs = {"_trigger_data": list_data}

    # Act
    result = await trigger_node.execute(inputs, node_execution_context)
    result = result.model_dump(exclude_none=True, by_alias=True)

    # Assert - list data should be preserved
    assert "trigger_data" in result
    assert result["trigger_data"] == list_data


@pytest.mark.asyncio
async def test_number_trigger_data(trigger_node, node_execution_context):
    """Test that numeric trigger data is preserved as-is."""
    # Arrange
    inputs = {"_trigger_data": 42}

    # Act
    result = await trigger_node.execute(inputs, node_execution_context)
    result = result.model_dump(exclude_none=True, by_alias=True)

    # Assert - number data should be preserved
    assert "trigger_data" in result
    assert result["trigger_data"] == 42
