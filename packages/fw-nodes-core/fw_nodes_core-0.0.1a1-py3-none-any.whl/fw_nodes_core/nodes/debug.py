"""Debug node for inspecting data flowing through the pipeline."""

import json
from typing import Any, Optional

from flowire_sdk import BaseNode, BaseNodeOutput, NodeExecutionContext, NodeMetadata
from pydantic import BaseModel, Field


class DebugInput(BaseModel):
    data: Optional[str] = Field(None, description="Data to inspect. Use Insert button to reference data from other nodes. Leave empty to show all inputs.")
    label: Optional[str] = Field(None, description="Optional label for this debug point")


class DebugOutput(BaseNodeOutput):
    # Dynamic fields - inspected data fields are passed through
    metadata: dict[str, Any] = Field(default_factory=dict, description="Debug metadata")

    class Config:
        extra = "allow"


class DebugNode(BaseNode):
    """Debug node that inspects and displays data in execution results."""

    input_schema = DebugInput
    output_schema = DebugOutput

    metadata = NodeMetadata(
        name="Debug",
        description="Inspect data and show debug information in execution results",
        category="utility",
        icon="🐛",
        color="#607D8B",
    )

    def _get_data_summary(self, data: Any) -> dict[str, Any]:
        """Generate a summary of the data for debugging.

        Args:
            data: Data to summarize

        Returns:
            Dict with type info, size, preview, etc.
        """
        summary: dict[str, Any] = {}

        # Basic type info
        if data is None:
            summary["type"] = "null"
            summary["value"] = None

        elif isinstance(data, bool):
            summary["type"] = "bool"
            summary["value"] = data

        elif isinstance(data, int):
            summary["type"] = "int"
            summary["value"] = data

        elif isinstance(data, float):
            summary["type"] = "float"
            summary["value"] = data

        elif isinstance(data, str):
            summary["type"] = "str"
            summary["length"] = len(data)
            # Show preview (first 100 chars)
            if len(data) > 100:
                summary["preview"] = data[:100] + "..."
                summary["full_value_truncated"] = True
            else:
                summary["preview"] = data
                summary["full_value_truncated"] = False

        elif isinstance(data, list):
            summary["type"] = "list"
            summary["length"] = len(data)
            # Show first few items
            if len(data) > 0:
                summary["first_item_type"] = type(data[0]).__name__
                if len(data) <= 3:
                    summary["preview"] = data
                else:
                    summary["preview"] = data[:3]
                    summary["preview_truncated"] = True

        elif isinstance(data, dict):
            summary["type"] = "dict"
            summary["keys"] = list(data.keys())
            summary["key_count"] = len(data.keys())
            # Show first few key-value pairs
            if len(data) <= 5:
                summary["preview"] = data
            else:
                preview = {k: data[k] for k in list(data.keys())[:5]}
                summary["preview"] = preview
                summary["preview_truncated"] = True

        else:
            summary["type"] = type(data).__name__
            summary["value"] = str(data)

        # Try to show JSON representation for complex types
        if isinstance(data, (list, dict)):
            try:
                json_str = json.dumps(data, indent=2)
                if len(json_str) > 500:
                    summary["json_preview"] = json_str[:500] + "\n..."
                else:
                    summary["json_preview"] = json_str
            except (TypeError, ValueError):
                summary["json_preview"] = "Unable to serialize to JSON"

        return summary

    async def execute(
        self,
        inputs: dict[str, Any],
        context: NodeExecutionContext,
    ) -> dict[str, Any]:
        """Inspect data and return with debug info.

        Note: This method overrides BaseNode.execute() to use full expression parsing
        (parse_expressions) instead of schema-only parsing (parse_expressions_in_schema_fields).
        """
        # Parse expressions in inputs
        inputs = await self.parse_expressions(inputs, context)

        validated_inputs = self.validate_inputs(inputs)
        field_name = validated_inputs.get("data")  # This is the field name (string) or None
        label = validated_inputs.get("label")

        # Determine what data to inspect
        if field_name:
            # User specified a specific field to inspect (already parsed as expression)
            data_to_inspect = field_name
        else:
            # Default: show all config inputs (excluding the node's own config fields)
            data_to_inspect = {k: v for k, v in inputs.items() if k not in ("data", "label")}

        # Generate debug summary
        debug_summary = self._get_data_summary(data_to_inspect)

        # Build metadata
        metadata = {
            "summary": debug_summary,
            "node_id": context.node_id,
            "execution_id": str(context.execution_id),
        }
        if label:
            metadata["label"] = label
        if field_name:
            metadata["inspected_field"] = "data_expression"
        else:
            metadata["inspected_field"] = "all_inputs"

        # Flatten output: spread inspected data + metadata
        if isinstance(data_to_inspect, dict):
            # Spread the dict fields at top level, add metadata
            return DebugOutput(**data_to_inspect, metadata=metadata)
        else:
            # For non-dict data, add as "inspected_value" field
            return DebugOutput(inspected_value=data_to_inspect, metadata=metadata)
