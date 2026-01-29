"""Condition node for branching logic."""

import re
from enum import Enum
from typing import Any

from flowire_sdk import (
    BaseNode,
    BaseNodeOutput,
    HandleConfig,
    NodeExecutionContext,
    NodeHandles,
    NodeMetadata,
)
from pydantic import BaseModel, Field


class ComparisonOperator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"
    IS_TRUE = "is_true"
    IS_FALSE = "is_false"
    MATCHES_REGEX = "matches_regex"
    NOT_MATCHES_REGEX = "not_matches_regex"


class ConditionInput(BaseModel):
    value1: Any = Field(
        ...,  # Required
        description="First value to compare.",
    )
    operator: ComparisonOperator = Field(..., description="Comparison operator")
    value2: Any = Field(
        None,
        description="Second value to compare against (not needed for is_* operators).",
    )


class ConditionOutput(BaseNodeOutput):
    """Output contains only routing metadata (no data passthrough)."""

    pass


class ConditionNode(BaseNode):
    """Evaluates a condition and outputs true/false for branching."""

    input_schema = ConditionInput
    output_schema = ConditionOutput

    metadata = NodeMetadata(
        name="Condition",
        description=(
            "Evaluate a condition for branching logic"
            "Automatically converts to number if possible (e.g., '4' becomes 4.0). "
            'Wrap in quotes to force string comparison: "34" or \'34\' keeps as string "34". '
            'Use nested quotes for literal quotes: ""hello"" becomes string "hello".'
        ),
        category="logic",
        icon="🔀",
        color="#FF9800",
        handles=NodeHandles(
            inputs=[HandleConfig(id="default", position="left")],
            outputs=[
                HandleConfig(id="true", label="True", position="right"),
                HandleConfig(id="false", label="False", position="right"),
            ],
            routing_mode="conditional",
        ),
    )

    def _is_empty(self, value: Any) -> bool:
        """Check if value is empty (None, empty string, empty list, empty dict)."""
        if value is None:
            return True
        elif isinstance(value, (str, list, dict)):
            return len(value) == 0
        else:
            # For numbers, booleans, etc., consider 0 and False as empty
            return not bool(value)

    def _is_not_empty(self, value: Any) -> bool:
        """Check if value is NOT empty."""
        return not self._is_empty(value)

    def _auto_cast_compare_value(self, value: Any) -> Any:
        """
        Attempt to auto-cast compare value to float for numeric comparisons.
        If value is wrapped in quotes, strip outer quotes and keep as string.
        If casting fails, return original value as string.

        Examples:
            "34" or '34' → "34" (string, no casting)
            34 → 34.0 (float)
            ""hello"" → "hello" (string with quotes)
        """
        if value is None:
            return value

        # Check if value is a string wrapped in quotes (single or double)
        # If so, strip outer quotes and return as string (skip float casting)
        if isinstance(value, str) and len(value) >= 2:
            if (value[0] == value[-1]) and (value[0] in ('"', "'")):
                # Strip outer quotes and return as explicit string
                return value[1:-1]

        # Try to convert to float
        try:
            return float(value)
        except (ValueError, TypeError):
            # Keep as original value (likely string)
            return value

    def _auto_cast_value_to_match(self, value: Any, compare_value: Any) -> Any:
        """Try to auto-cast value to match compare_value's type for comparison.

        If compare_value is a number and value is a string number, convert it.
        Otherwise return value as-is.
        """
        # If compare_value is a number and value is a string, try to convert
        if isinstance(compare_value, (int, float)) and isinstance(value, str):
            try:
                # Try to convert string to the same type as compare_value
                if isinstance(compare_value, int):
                    return int(value)
                else:
                    return float(value)
            except (ValueError, TypeError):
                # Can't convert, return as-is
                return value

        return value

    def _evaluate_condition(self, value: Any, operator: ComparisonOperator, compare_value: Any) -> bool:
        """Evaluate condition using operator mapping."""
        # Operations that don't need compare_value
        simple_ops = {
            ComparisonOperator.IS_EMPTY: lambda v: self._is_empty(v),
            ComparisonOperator.IS_NOT_EMPTY: lambda v: self._is_not_empty(v),
            ComparisonOperator.IS_TRUE: lambda v: bool(v) is True,
            ComparisonOperator.IS_FALSE: lambda v: bool(v) is False,
        }

        # Operations that need compare_value
        comparison_ops = {
            ComparisonOperator.EQUALS: lambda v, cv: v == cv,
            ComparisonOperator.NOT_EQUALS: lambda v, cv: v != cv,
            ComparisonOperator.GREATER_THAN: lambda v, cv: v > cv,
            ComparisonOperator.LESS_THAN: lambda v, cv: v < cv,
            ComparisonOperator.GREATER_THAN_OR_EQUAL: lambda v, cv: v >= cv,
            ComparisonOperator.LESS_THAN_OR_EQUAL: lambda v, cv: v <= cv,
            ComparisonOperator.CONTAINS: lambda v, cv: cv in v,
            ComparisonOperator.NOT_CONTAINS: lambda v, cv: cv not in v,
            ComparisonOperator.IN: lambda v, cv: v in cv,
            ComparisonOperator.NOT_IN: lambda v, cv: v not in cv,
        }

        # Regex operations
        if operator == ComparisonOperator.MATCHES_REGEX:
            try:
                return bool(re.search(compare_value, str(value)))
            except re.error as e:
                raise ValueError(f"Invalid regex pattern '{compare_value}': {e}")

        if operator == ComparisonOperator.NOT_MATCHES_REGEX:
            try:
                return not bool(re.search(compare_value, str(value)))
            except re.error as e:
                raise ValueError(f"Invalid regex pattern '{compare_value}': {e}")

        if operator in simple_ops:
            return simple_ops[operator](value)
        elif operator in comparison_ops:
            # Try to auto-cast value to match compare_value type
            casted_value = self._auto_cast_value_to_match(value, compare_value)

            try:
                return comparison_ops[operator](casted_value, compare_value)
            except TypeError as e:
                # Provide helpful error message for type mismatches
                value_type = type(casted_value).__name__
                compare_type = type(compare_value).__name__
                raise TypeError(
                    f"Cannot compare {value_type} with {compare_type}. "
                    f"Field value is '{casted_value}' ({value_type}), "
                    f"compare value is '{compare_value}' ({compare_type}). "
                    f"Consider extracting the field as a number first or using a compatible comparison value."
                ) from e
        else:
            raise ValueError(f"Unknown operator: {operator}")

    async def execute_logic(
        self,
        validated_inputs: dict[str, Any],
        context: NodeExecutionContext,
    ) -> ConditionOutput:
        """Evaluate condition using value1 and value2."""
        # Auto-cast BOTH values symmetrically
        value1 = self._auto_cast_compare_value(validated_inputs["value1"])
        value2 = self._auto_cast_compare_value(validated_inputs.get("value2"))
        operator = validated_inputs["operator"]

        # Evaluate condition (type matching happens inside _evaluate_condition)
        condition_result = self._evaluate_condition(value1, operator, value2)

        # Return ONLY routing metadata (no data passthrough)
        return ConditionOutput(output_handle="true" if condition_result else "false")
