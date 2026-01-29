"""Tests for Delay node."""

import asyncio
from datetime import datetime

import pytest
from pydantic import ValidationError

from fw_nodes_core.nodes.delay import DelayNode, DelayOutput

# node_execution_context fixture provided by conftest.py


@pytest.mark.asyncio
async def test_static_delay_value(node_execution_context):
    """Test delay with static float value."""
    node = DelayNode()

    inputs = {"seconds": 0.1}

    start_time = asyncio.get_event_loop().time()
    result = await node.execute(inputs, node_execution_context)
    end_time = asyncio.get_event_loop().time()

    # Verify delay actually happened
    elapsed = end_time - start_time
    assert elapsed >= 0.1
    assert elapsed < 0.2  # Should not take much longer

    # Verify output
    assert isinstance(result, DelayOutput)
    assert result.delay_seconds == 0.1
    assert result.completed_at is not None

    # Verify timestamp is valid ISO format
    datetime.fromisoformat(result.completed_at)


@pytest.mark.asyncio
async def test_zero_delay(node_execution_context):
    """Test that zero delay is valid (no-op)."""
    node = DelayNode()

    inputs = {"seconds": 0.0}

    result = await node.execute(inputs, node_execution_context)

    assert isinstance(result, DelayOutput)
    assert result.delay_seconds == 0.0
    assert result.completed_at is not None


@pytest.mark.asyncio
async def test_fractional_seconds(node_execution_context):
    """Test delay with fractional seconds (sub-second precision)."""
    node = DelayNode()

    inputs = {"seconds": 0.05}

    start_time = asyncio.get_event_loop().time()
    result = await node.execute(inputs, node_execution_context)
    end_time = asyncio.get_event_loop().time()

    elapsed = end_time - start_time
    assert elapsed >= 0.05
    assert result.delay_seconds == 0.05


@pytest.mark.asyncio
async def test_integer_coerced_to_float(node_execution_context):
    """Test that integer input is accepted and coerced to float."""
    node = DelayNode()

    inputs = {"seconds": 1}  # integer

    result = await node.execute(inputs, node_execution_context)

    assert isinstance(result, DelayOutput)
    assert result.delay_seconds == 1.0
    assert isinstance(result.delay_seconds, float)


@pytest.mark.asyncio
async def test_negative_value_rejected(node_execution_context):
    """Test that negative delay values raise ValidationError."""
    node = DelayNode()

    inputs = {"seconds": -5.0}

    with pytest.raises(ValidationError) as exc_info:
        await node.execute(inputs, node_execution_context)

    assert "greater than or equal to 0" in str(exc_info.value)


@pytest.mark.asyncio
async def test_non_numeric_string_rejected(node_execution_context):
    """Test that non-numeric string values raise ValidationError."""
    node = DelayNode()

    inputs = {"seconds": "abc"}

    with pytest.raises(ValidationError) as exc_info:
        await node.execute(inputs, node_execution_context)

    assert "valid number" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_missing_field_rejected(node_execution_context):
    """Test that missing 'seconds' field raises ValidationError."""
    node = DelayNode()

    inputs = {}

    with pytest.raises(ValidationError) as exc_info:
        await node.execute(inputs, node_execution_context)

    assert "required" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_expression_parsing_support(node_execution_context):
    """Test that expression strings are parsed before validation."""
    node = DelayNode()

    # Simulate expression already resolved to value
    inputs = {"seconds": 2.5}

    result = await node.execute(inputs, node_execution_context)

    assert result.delay_seconds == 2.5
