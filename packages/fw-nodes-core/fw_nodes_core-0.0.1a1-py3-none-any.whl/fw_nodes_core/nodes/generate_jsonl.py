"""Generate JSONL (JSON Lines) file from list data."""

import json
from typing import Any

from flowire_sdk import BaseNode, BaseNodeOutput, NodeExecutionContext, NodeMetadata
from pydantic import BaseModel, Field


class GenerateJSONLInput(BaseModel):
    data: list[Any] = Field(..., description="List of items to convert to JSONL. Use Insert button to reference data from other nodes.")


class GenerateJSONLOutput(BaseNodeOutput):
    storage_ref: dict[str, Any] = Field(..., description="Storage reference to the JSONL file")
    line_count: int = Field(..., description="Number of lines in the JSONL file")
    size_bytes: int = Field(..., description="Size of the output in bytes")


class GenerateJSONLNode(BaseNode):
    """Convert a list of objects into JSONL (JSON Lines) format."""

    input_schema = GenerateJSONLInput
    output_schema = GenerateJSONLOutput

    metadata = NodeMetadata(
        name="Generate JSONL",
        description="Convert a list of objects to JSONL (JSON Lines) format",
        category="data",
        icon="📄",
        color="#FF9800",
    )

    async def execute_logic(
        self,
        validated_inputs: dict[str, Any],
        context: NodeExecutionContext,
    ) -> dict[str, Any]:
        """Generate JSONL file from list data."""
        data = validated_inputs.get("data")
        if not isinstance(data, list):
            raise ValueError(f"Data must be a list, got {type(data).__name__}")

        # Convert each item to JSON and join with newlines
        jsonl_lines = []
        for item in data:
            try:
                json_line = json.dumps(item, ensure_ascii=False)
                jsonl_lines.append(json_line)
            except (TypeError, ValueError) as e:
                raise ValueError(f"Failed to serialize item to JSON: {e}") from e

        # Join with newlines to create JSONL format
        jsonl_content = "\n".join(jsonl_lines)

        # Convert to bytes for storage
        jsonl_bytes = jsonl_content.encode("utf-8")
        size_bytes = len(jsonl_bytes)

        # Store the JSONL file in storage (S3 or local) via context
        storage_ref = context.store_binary(
            data=jsonl_bytes,
            filename="output.jsonl",
            content_type="application/x-ndjson",
            metadata={
                "line_count": len(jsonl_lines),
                "size_bytes": size_bytes,
                "execution_id": context.execution_id,
                "node_id": context.node_id,
            },
        )

        # Return Pydantic instance
        return GenerateJSONLOutput(
            storage_ref=storage_ref,
            line_count=len(jsonl_lines),
            size_bytes=size_bytes,
        )
