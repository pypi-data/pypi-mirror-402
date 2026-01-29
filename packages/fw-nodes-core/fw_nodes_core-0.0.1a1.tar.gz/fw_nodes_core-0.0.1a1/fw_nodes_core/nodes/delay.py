"""Delay node for pausing workflow execution."""

import asyncio
from datetime import datetime, timezone
from typing import Any

from flowire_sdk import BaseNode, BaseNodeOutput, NodeExecutionContext, NodeMetadata
from pydantic import BaseModel, Field


class DelayInput(BaseModel):
    """Input schema for Delay node."""
    seconds: float = Field(
        ...,
        ge=0.0,
        description="Number of seconds to delay. Use Insert button to reference data from other nodes."
    )


class DelayOutput(BaseNodeOutput):
    """Output schema for Delay node with metadata."""
    delay_seconds: float = Field(..., description="Actual delay duration in seconds")
    completed_at: str = Field(..., description="ISO timestamp when delay completed")


class DelayNode(BaseNode):
    """Pause workflow execution for a specified duration."""

    input_schema = DelayInput
    output_schema = DelayOutput

    metadata = NodeMetadata(
        name="Delay",
        description="Pause workflow execution for a specified duration",
        category="utility",
        icon="⏱️",
        color="#9E9E9E",
    )

    async def execute_logic(
        self,
        validated_inputs: dict[str, Any],
        context: NodeExecutionContext,
    ) -> DelayOutput:
        """Execute delay and return metadata.

        Args:
            validated_inputs: Validated input containing 'seconds' field
            context: Node execution context

        Returns:
            DelayOutput with delay metadata
        """
        delay_seconds = validated_inputs["seconds"]

        # Perform the async delay
        await asyncio.sleep(delay_seconds)

        # Capture completion timestamp
        completed_at = datetime.now(timezone.utc).isoformat()

        return DelayOutput(
            delay_seconds=delay_seconds,
            completed_at=completed_at
        )
