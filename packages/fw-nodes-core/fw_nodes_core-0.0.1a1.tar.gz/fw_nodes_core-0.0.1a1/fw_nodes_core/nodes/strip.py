"""Strip whitespace from strings."""

from typing import Any

from flowire_sdk import BaseNode, BaseNodeOutput, NodeExecutionContext, NodeMetadata
from pydantic import BaseModel, Field


class StripInput(BaseModel):
    text: str = Field(..., description="Text to strip. Use Insert button to reference data from other nodes.")


class StripOutput(BaseNodeOutput):
    text: str = Field(..., description="Text with whitespace removed from both sides")


class StripNode(BaseNode):
    """Remove whitespace from both sides of a string."""

    input_schema = StripInput
    output_schema = StripOutput

    metadata = NodeMetadata(
        name="Strip",
        description="Remove whitespace from both sides of a string",
        category="data",
        icon="✂️",
        color="#607D8B",
    )

    async def execute_logic(
        self,
        validated_inputs: dict[str, Any],
        context: NodeExecutionContext,
    ) -> dict[str, Any]:
        """Strip whitespace from text."""
        text = validated_inputs.get("text")
        if not isinstance(text, str):
            raise ValueError(f"Text must be a string, got {type(text).__name__}")

        # Strip whitespace from both sides
        stripped = text.strip()

        # Return Pydantic instance
        return StripOutput(text=stripped)
