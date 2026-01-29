"""Return node for returning values to calling workflow."""

import json
from typing import Any

from flowire_sdk import BaseNode, BaseNodeOutput, HandleConfig, NodeExecutionContext, NodeHandles, NodeMetadata
from pydantic import BaseModel, Field


class KeyValuePair(BaseModel):
    """Single key-value pair definition."""
    key: str = Field(..., description="Return field name", min_length=1)
    value: Any = Field(..., description="Value to return. Use Insert button to reference data from other nodes.")


class ReturnInput(BaseModel):
    """Input schema with list of key-value pairs."""
    pairs: list[KeyValuePair] = Field(
        default_factory=list,
        description="Key-value pairs to return to caller",
    )


class ReturnOutput(BaseNodeOutput):
    """Output schema with dynamic fields from user-defined keys."""

    class Config:
        extra = "allow"  # Allow arbitrary fields from key-value pairs


class ReturnNode(BaseNode):
    """Return values to the calling workflow (Call Flow or For Each)."""

    input_schema = ReturnInput
    output_schema = ReturnOutput

    metadata = NodeMetadata(
        name="Return",
        description="Return values to the calling workflow (Call Flow or For Each)",
        category="logic",
        icon="↩️",
        color="#FF5722",
        handles=NodeHandles(
            inputs=[HandleConfig(id="default", position="left")],
            outputs=[],  # Terminal node - no outputs
        ),
    )

    async def execute_logic(
        self,
        validated_inputs: dict[str, Any],
        context: NodeExecutionContext,
    ) -> ReturnOutput:
        """Build output object from key-value pairs.

        - Validates unique keys
        - Attempts to parse values as JSON (objects/arrays)
        - Falls back to string if JSON parsing fails
        - Returns flat object with all key-value pairs
        """
        pairs = validated_inputs.get("pairs", [])

        # Validate unique keys (defense in depth - UI also validates)
        keys_seen = set()
        duplicate_keys = []
        for pair in pairs:
            if pair["key"] in keys_seen:
                duplicate_keys.append(pair["key"])
            keys_seen.add(pair["key"])

        if duplicate_keys:
            raise ValueError(
                f"Duplicate keys found: {', '.join(duplicate_keys)}. "
                "Each key must be unique."
            )

        # Build output object
        output_dict = {}
        for pair in pairs:
            value = pair["value"]

            # Try to parse as JSON if it looks like JSON
            if isinstance(value, str) and value.strip().startswith(('{', '[')):
                try:
                    value = json.loads(value)
                except (json.JSONDecodeError, ValueError):
                    # Not valid JSON, keep as string
                    pass

            output_dict[pair["key"]] = value

        return ReturnOutput(**output_dict)
