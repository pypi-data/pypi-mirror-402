"""Tests for Call Flow node."""
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from flowire_sdk import NodeExecutionContext

from fw_nodes_core.nodes.call_flow import CallFlowNode


@pytest.fixture
def mock_context():
    """Create a mock NodeExecutionContext with execute_subworkflow."""
    context = MagicMock(spec=NodeExecutionContext)
    context.workflow_id = str(uuid4())
    context.execution_id = str(uuid4())
    context.node_id = "test_node"
    context.project_id = str(uuid4())
    context.user_id = str(uuid4())
    context.node_results = {}
    return context


@pytest.mark.asyncio
async def test_call_flow_waits_for_completion(mock_context):
    """Test that Call Flow waits for execution to complete."""
    target_workflow_id = str(uuid4())
    execution_id = str(uuid4())

    # Mock execute_subworkflow to return a result
    mock_context.execute_subworkflow = AsyncMock(return_value={
        "execution_id": execution_id,
        "return_value": None,
        "execution_time_ms": 50,
        "status": "completed",
    })

    node = CallFlowNode()
    inputs = {
        "target_workflow_id": target_workflow_id,
        "target_node_id": "trigger1",
        "call_data": {"test": "data"}
    }

    result = await node.execute(inputs, mock_context)
    result_dict = result.model_dump(exclude_none=True)

    # Should have metadata under 'meta' key
    assert "meta" in result_dict
    assert "execution_id" in result_dict["meta"]
    assert "triggered" in result_dict["meta"]
    assert result_dict["meta"]["triggered"] is True

    # Verify execute_subworkflow was called correctly
    mock_context.execute_subworkflow.assert_called_once()
    call_kwargs = mock_context.execute_subworkflow.call_args[1]
    assert call_kwargs["workflow_id"] == target_workflow_id
    assert call_kwargs["wait_for_completion"] is True


@pytest.mark.asyncio
async def test_call_flow_returns_result(mock_context):
    """Test that Call Flow returns the called workflow's result."""
    target_workflow_id = str(uuid4())
    execution_id = str(uuid4())

    # Mock execute_subworkflow to return a result with return_value
    mock_context.execute_subworkflow = AsyncMock(return_value={
        "execution_id": execution_id,
        "return_value": {"message": "result_value"},
        "execution_time_ms": 100,
        "status": "completed",
    })

    node = CallFlowNode()
    inputs = {
        "target_workflow_id": target_workflow_id,
        "target_node_id": "trigger1",
        "call_data": {}
    }

    result = await node.execute(inputs, mock_context)
    result_dict = result.model_dump(exclude_none=True)

    # Should contain the Return node data spread at top level
    assert "message" in result_dict
    assert result_dict["message"] == "result_value"
    # Metadata should be under 'meta'
    assert "meta" in result_dict
    assert result_dict["meta"]["triggered"] is True


@pytest.mark.asyncio
async def test_call_flow_timeout(mock_context):
    """Test that Call Flow raises error when sub-workflow times out."""
    target_workflow_id = str(uuid4())

    # Mock execute_subworkflow to raise timeout error
    mock_context.execute_subworkflow = AsyncMock(
        side_effect=ValueError("Call timed out after 1.0s. Execution test-exec still running.")
    )

    node = CallFlowNode()
    node.max_wait_seconds = 1.0
    inputs = {
        "target_workflow_id": target_workflow_id,
        "target_node_id": "trigger1",
        "call_data": {}
    }

    with pytest.raises(ValueError, match="Call timed out"):
        await node.execute(inputs, mock_context)


@pytest.mark.asyncio
async def test_call_flow_propagates_errors(mock_context):
    """Test that Call Flow propagates errors from called workflows."""
    target_workflow_id = str(uuid4())

    # Mock execute_subworkflow to raise error from failed workflow
    mock_context.execute_subworkflow = AsyncMock(
        side_effect=ValueError("Called workflow failed: HTTP request failed: Connection error")
    )

    node = CallFlowNode()
    inputs = {
        "target_workflow_id": target_workflow_id,
        "target_node_id": "trigger1",
        "call_data": {}
    }

    with pytest.raises(ValueError, match="Called workflow failed"):
        await node.execute(inputs, mock_context)


@pytest.mark.asyncio
async def test_call_flow_requires_target_workflow_id(mock_context):
    """Test that Call Flow requires target_workflow_id."""
    node = CallFlowNode()
    inputs = {
        "target_workflow_id": "",
        "target_node_id": "trigger1",
        "call_data": {}
    }

    with pytest.raises(ValueError, match="target_workflow_id and target_node_id are required"):
        await node.execute(inputs, mock_context)


@pytest.mark.asyncio
async def test_call_flow_requires_target_node_id(mock_context):
    """Test that Call Flow requires target_node_id."""
    node = CallFlowNode()
    inputs = {
        "target_workflow_id": str(uuid4()),
        "target_node_id": "",
        "call_data": {}
    }

    with pytest.raises(ValueError, match="target_workflow_id and target_node_id are required"):
        await node.execute(inputs, mock_context)


@pytest.mark.asyncio
async def test_call_flow_passes_version_to_context(mock_context):
    """Test that Call Flow passes version to execute_subworkflow."""
    target_workflow_id = str(uuid4())
    execution_id = str(uuid4())

    mock_context.execute_subworkflow = AsyncMock(return_value={
        "execution_id": execution_id,
        "return_value": None,
        "execution_time_ms": 50,
        "status": "completed",
    })

    node = CallFlowNode()
    inputs = {
        "target_workflow_id": target_workflow_id,
        "target_node_id": "trigger1",
        "call_data": {},
        "version": "default"
    }

    await node.execute(inputs, mock_context)

    # Verify version was passed
    call_kwargs = mock_context.execute_subworkflow.call_args[1]
    assert call_kwargs["trigger_data"]["version"] == "default"


@pytest.mark.asyncio
async def test_call_flow_none_result_raises_error(mock_context):
    """Test that None result from execute_subworkflow raises error."""
    mock_context.execute_subworkflow = AsyncMock(return_value=None)

    node = CallFlowNode()
    inputs = {
        "target_workflow_id": str(uuid4()),
        "target_node_id": "trigger1",
        "call_data": {}
    }

    with pytest.raises(ValueError, match="Sub-workflow execution returned no result"):
        await node.execute(inputs, mock_context)


@pytest.mark.asyncio
async def test_call_flow_meta_key_conflict():
    """Test that Call Flow raises error if return value contains 'meta' key."""
    mock_context = MagicMock(spec=NodeExecutionContext)
    mock_context.execute_subworkflow = AsyncMock(return_value={
        "execution_id": str(uuid4()),
        "return_value": {"meta": "this should conflict"},
        "execution_time_ms": 50,
        "status": "completed",
    })

    node = CallFlowNode()
    inputs = {
        "target_workflow_id": str(uuid4()),
        "target_node_id": "trigger1",
        "call_data": {}
    }

    with pytest.raises(ValueError, match="Return node cannot use 'meta' as a key"):
        await node.execute(inputs, mock_context)
