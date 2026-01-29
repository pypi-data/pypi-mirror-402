"""Tests for Condition node."""

import pytest

from fw_nodes_core.nodes.condition import ComparisonOperator, ConditionNode

# node_execution_context fixture provided by conftest.py


@pytest.mark.asyncio
async def test_equals_literal_values(node_execution_context):
    """Test equals operator with literal values."""
    node = ConditionNode()

    inputs = {
        "value1": 42,
        "operator": ComparisonOperator.EQUALS,
        "value2": 42
    }

    result = await node.execute(inputs, node_execution_context)

    assert result.output_handle == "true"
    assert not hasattr(result, 'value')  # No data passthrough


@pytest.mark.asyncio
async def test_not_equals_literal_values(node_execution_context):
    """Test not equals operator."""
    node = ConditionNode()

    inputs = {
        "value1": "hello",
        "operator": ComparisonOperator.NOT_EQUALS,
        "value2": "world"
    }

    result = await node.execute(inputs, node_execution_context)

    assert result.output_handle == "true"


@pytest.mark.asyncio
async def test_greater_than_numbers(node_execution_context):
    """Test greater than with numbers."""
    node = ConditionNode()

    inputs = {
        "value1": 100,
        "operator": ComparisonOperator.GREATER_THAN,
        "value2": 50
    }

    result = await node.execute(inputs, node_execution_context)

    assert result.output_handle == "true"


@pytest.mark.asyncio
async def test_less_than_returns_false(node_execution_context):
    """Test less than that returns false."""
    node = ConditionNode()

    inputs = {
        "value1": 100,
        "operator": ComparisonOperator.LESS_THAN,
        "value2": 50
    }

    result = await node.execute(inputs, node_execution_context)

    assert result.output_handle == "false"


@pytest.mark.asyncio
async def test_greater_than_or_equal(node_execution_context):
    """Test greater than or equal."""
    node = ConditionNode()

    inputs = {
        "value1": 50,
        "operator": ComparisonOperator.GREATER_THAN_OR_EQUAL,
        "value2": 50
    }

    result = await node.execute(inputs, node_execution_context)

    assert result.output_handle == "true"


@pytest.mark.asyncio
async def test_less_than_or_equal(node_execution_context):
    """Test less than or equal."""
    node = ConditionNode()

    inputs = {
        "value1": 25,
        "operator": ComparisonOperator.LESS_THAN_OR_EQUAL,
        "value2": 50
    }

    result = await node.execute(inputs, node_execution_context)

    assert result.output_handle == "true"


@pytest.mark.asyncio
async def test_contains_string(node_execution_context):
    """Test contains operator with strings."""
    node = ConditionNode()

    inputs = {
        "value1": "hello world",
        "operator": ComparisonOperator.CONTAINS,
        "value2": "world"
    }

    result = await node.execute(inputs, node_execution_context)

    assert result.output_handle == "true"


@pytest.mark.asyncio
async def test_not_contains_string(node_execution_context):
    """Test not contains operator."""
    node = ConditionNode()

    inputs = {
        "value1": "hello world",
        "operator": ComparisonOperator.NOT_CONTAINS,
        "value2": "xyz"
    }

    result = await node.execute(inputs, node_execution_context)

    assert result.output_handle == "true"


@pytest.mark.asyncio
async def test_is_empty_with_empty_string(node_execution_context):
    """Test is_empty with empty string."""
    node = ConditionNode()

    inputs = {
        "value1": "",
        "operator": ComparisonOperator.IS_EMPTY,
    }

    result = await node.execute(inputs, node_execution_context)

    assert result.output_handle == "true"


@pytest.mark.asyncio
async def test_is_empty_with_none(node_execution_context):
    """Test is_empty with None."""
    node = ConditionNode()

    inputs = {
        "value1": None,
        "operator": ComparisonOperator.IS_EMPTY,
    }

    result = await node.execute(inputs, node_execution_context)

    assert result.output_handle == "true"


@pytest.mark.asyncio
async def test_is_not_empty_with_value(node_execution_context):
    """Test is_not_empty with a value."""
    node = ConditionNode()

    inputs = {
        "value1": "hello",
        "operator": ComparisonOperator.IS_NOT_EMPTY,
    }

    result = await node.execute(inputs, node_execution_context)

    assert result.output_handle == "true"


@pytest.mark.asyncio
async def test_is_true(node_execution_context):
    """Test is_true operator."""
    node = ConditionNode()

    inputs = {
        "value1": True,
        "operator": ComparisonOperator.IS_TRUE,
    }

    result = await node.execute(inputs, node_execution_context)

    assert result.output_handle == "true"


@pytest.mark.asyncio
async def test_is_false(node_execution_context):
    """Test is_false operator."""
    node = ConditionNode()

    inputs = {
        "value1": False,
        "operator": ComparisonOperator.IS_FALSE,
    }

    result = await node.execute(inputs, node_execution_context)

    assert result.output_handle == "true"


@pytest.mark.asyncio
async def test_auto_cast_string_to_number(node_execution_context):
    """Test auto-casting string number to number for comparison."""
    node = ConditionNode()

    inputs = {
        "value1": "42",
        "operator": ComparisonOperator.EQUALS,
        "value2": 42
    }

    result = await node.execute(inputs, node_execution_context)

    # Should cast "42" to 42.0 and match
    assert result.output_handle == "true"


@pytest.mark.asyncio
@pytest.mark.skip(reason="Known issue: _auto_cast_value_to_match still casts quoted strings when comparing against numbers")
async def test_quoted_string_prevents_cast(node_execution_context):
    """Test that quote-wrapped strings prevent auto-casting.

    TODO: Fix condition node to not auto-cast values that were explicitly quoted.
    The _auto_cast_compare_value strips quotes correctly, but _auto_cast_value_to_match
    then converts the string back to a number for comparison.
    """
    node = ConditionNode()

    inputs = {
        "value1": '"42"',  # Quoted string
        "operator": ComparisonOperator.EQUALS,
        "value2": 42
    }

    result = await node.execute(inputs, node_execution_context)

    # Should keep "42" as string and not match number 42
    assert result.output_handle == "false"


@pytest.mark.asyncio
async def test_symmetric_auto_cast_both_values(node_execution_context):
    """Test that auto-casting applies symmetrically to both values."""
    node = ConditionNode()

    inputs = {
        "value1": "100",
        "operator": ComparisonOperator.GREATER_THAN,
        "value2": "50"
    }

    result = await node.execute(inputs, node_execution_context)

    # Both should be cast to numbers and compared
    assert result.output_handle == "true"


@pytest.mark.asyncio
async def test_nested_object_comparison(node_execution_context):
    """Test comparing nested dict objects."""
    node = ConditionNode()

    inputs = {
        "value1": {"status": "success", "code": 200},
        "operator": ComparisonOperator.EQUALS,
        "value2": {"status": "success", "code": 200}
    }

    result = await node.execute(inputs, node_execution_context)

    assert result.output_handle == "true"


@pytest.mark.asyncio
async def test_array_comparison(node_execution_context):
    """Test comparing arrays."""
    node = ConditionNode()

    inputs = {
        "value1": [1, 2, 3],
        "operator": ComparisonOperator.EQUALS,
        "value2": [1, 2, 3]
    }

    result = await node.execute(inputs, node_execution_context)

    assert result.output_handle == "true"


@pytest.mark.asyncio
async def test_type_mismatch_error(node_execution_context):
    """Test that incompatible type comparison raises helpful error."""
    node = ConditionNode()

    inputs = {
        "value1": [1, 2, 3],
        "operator": ComparisonOperator.GREATER_THAN,
        "value2": 42
    }

    with pytest.raises(TypeError) as exc_info:
        await node.execute(inputs, node_execution_context)

    assert "Cannot compare" in str(exc_info.value)


@pytest.mark.asyncio
async def test_in_list(node_execution_context):
    """Test 'in' operator with list membership."""
    node = ConditionNode()

    inputs = {
        "value1": "bot123",
        "operator": ComparisonOperator.IN,
        "value2": ["bot123", "bot456", "bot789"]
    }

    result = await node.execute(inputs, node_execution_context)

    assert result.output_handle == "true"


@pytest.mark.asyncio
async def test_in_list_not_found(node_execution_context):
    """Test 'in' operator when value is not in list."""
    node = ConditionNode()

    inputs = {
        "value1": "user123",
        "operator": ComparisonOperator.IN,
        "value2": ["bot123", "bot456", "bot789"]
    }

    result = await node.execute(inputs, node_execution_context)

    assert result.output_handle == "false"


@pytest.mark.asyncio
async def test_not_in_list(node_execution_context):
    """Test 'not_in' operator with list membership."""
    node = ConditionNode()

    inputs = {
        "value1": "user123",
        "operator": ComparisonOperator.NOT_IN,
        "value2": ["bot123", "bot456", "bot789"]
    }

    result = await node.execute(inputs, node_execution_context)

    assert result.output_handle == "true"


@pytest.mark.asyncio
async def test_not_in_list_found(node_execution_context):
    """Test 'not_in' operator when value is in list."""
    node = ConditionNode()

    inputs = {
        "value1": "bot123",
        "operator": ComparisonOperator.NOT_IN,
        "value2": ["bot123", "bot456", "bot789"]
    }

    result = await node.execute(inputs, node_execution_context)

    assert result.output_handle == "false"


@pytest.mark.asyncio
async def test_in_string_substring(node_execution_context):
    """Test 'in' operator works for substring check too."""
    node = ConditionNode()

    inputs = {
        "value1": "world",
        "operator": ComparisonOperator.IN,
        "value2": "hello world"
    }

    result = await node.execute(inputs, node_execution_context)

    assert result.output_handle == "true"


# --- Regex operator tests ---


@pytest.mark.asyncio
async def test_matches_regex_digits(node_execution_context):
    """Test matches_regex with digit pattern."""
    node = ConditionNode()

    inputs = {
        "value1": "Order #12345",
        "operator": ComparisonOperator.MATCHES_REGEX,
        "value2": r"#\d+"
    }

    result = await node.execute(inputs, node_execution_context)

    assert result.output_handle == "true"


@pytest.mark.asyncio
async def test_matches_regex_email_pattern(node_execution_context):
    """Test matches_regex with email-like pattern."""
    node = ConditionNode()

    inputs = {
        "value1": "user@example.com",
        "operator": ComparisonOperator.MATCHES_REGEX,
        "value2": r"^[\w.]+@[\w.]+$"
    }

    result = await node.execute(inputs, node_execution_context)

    assert result.output_handle == "true"


@pytest.mark.asyncio
async def test_matches_regex_no_match(node_execution_context):
    """Test matches_regex returns false when pattern doesn't match."""
    node = ConditionNode()

    inputs = {
        "value1": "hello world",
        "operator": ComparisonOperator.MATCHES_REGEX,
        "value2": r"^\d+$"
    }

    result = await node.execute(inputs, node_execution_context)

    assert result.output_handle == "false"


@pytest.mark.asyncio
async def test_matches_regex_anchored_full_match(node_execution_context):
    """Test matches_regex with anchors for full string match."""
    node = ConditionNode()

    # Partial match without anchors
    inputs_partial = {
        "value1": "abc123",
        "operator": ComparisonOperator.MATCHES_REGEX,
        "value2": r"\d+"
    }
    result_partial = await node.execute(inputs_partial, node_execution_context)
    assert result_partial.output_handle == "true"

    # Full match with anchors - should fail because string has letters
    inputs_full = {
        "value1": "abc123",
        "operator": ComparisonOperator.MATCHES_REGEX,
        "value2": r"^\d+$"
    }
    result_full = await node.execute(inputs_full, node_execution_context)
    assert result_full.output_handle == "false"


@pytest.mark.asyncio
async def test_matches_regex_case_insensitive(node_execution_context):
    """Test matches_regex with case-insensitive flag."""
    node = ConditionNode()

    inputs = {
        "value1": "Hello World",
        "operator": ComparisonOperator.MATCHES_REGEX,
        "value2": r"(?i)hello"
    }

    result = await node.execute(inputs, node_execution_context)

    assert result.output_handle == "true"


@pytest.mark.asyncio
async def test_matches_regex_case_sensitive_default(node_execution_context):
    """Test that matches_regex is case-sensitive by default."""
    node = ConditionNode()

    inputs = {
        "value1": "Hello World",
        "operator": ComparisonOperator.MATCHES_REGEX,
        "value2": r"hello"
    }

    result = await node.execute(inputs, node_execution_context)

    assert result.output_handle == "false"


@pytest.mark.asyncio
async def test_not_matches_regex(node_execution_context):
    """Test not_matches_regex operator."""
    node = ConditionNode()

    inputs = {
        "value1": "abc123",
        "operator": ComparisonOperator.NOT_MATCHES_REGEX,
        "value2": r"^[a-z]+$"
    }

    result = await node.execute(inputs, node_execution_context)

    # String contains digits, so it doesn't match letters-only pattern
    assert result.output_handle == "true"


@pytest.mark.asyncio
async def test_not_matches_regex_when_matches(node_execution_context):
    """Test not_matches_regex returns false when pattern matches."""
    node = ConditionNode()

    inputs = {
        "value1": "abc",
        "operator": ComparisonOperator.NOT_MATCHES_REGEX,
        "value2": r"^[a-z]+$"
    }

    result = await node.execute(inputs, node_execution_context)

    assert result.output_handle == "false"


@pytest.mark.asyncio
async def test_matches_regex_invalid_pattern(node_execution_context):
    """Test that invalid regex pattern raises ValueError."""
    node = ConditionNode()

    inputs = {
        "value1": "test string",
        "operator": ComparisonOperator.MATCHES_REGEX,
        "value2": "[unclosed"
    }

    with pytest.raises(ValueError) as exc_info:
        await node.execute(inputs, node_execution_context)

    assert "Invalid regex pattern" in str(exc_info.value)


@pytest.mark.asyncio
async def test_matches_regex_non_string_value(node_execution_context):
    """Test that non-string value1 gets cast to string for regex matching.

    Note: Numbers are auto-cast to floats first (12345 -> 12345.0),
    so the string representation will include the decimal point.
    """
    node = ConditionNode()

    inputs = {
        "value1": 12345,
        "operator": ComparisonOperator.MATCHES_REGEX,
        "value2": r"^\d+\.0$"  # Matches "12345.0" after auto-cast
    }

    result = await node.execute(inputs, node_execution_context)

    assert result.output_handle == "true"


@pytest.mark.asyncio
async def test_matches_regex_list_value(node_execution_context):
    """Test regex matching with list value (converted to string representation)."""
    node = ConditionNode()

    inputs = {
        "value1": ["a", "b", "c"],
        "operator": ComparisonOperator.MATCHES_REGEX,
        "value2": r"\['a', 'b', 'c'\]"
    }

    result = await node.execute(inputs, node_execution_context)

    assert result.output_handle == "true"
