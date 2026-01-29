"""Group node for organizing and grouping other nodes visually."""

from typing import Any, Optional

from flowire_sdk import BaseNode, NodeExecutionContext, NodeHandles, NodeMetadata
from pydantic import BaseModel, Field


class GroupInput(BaseModel):
    """Group node has no required inputs - it's a visual container."""

    backgroundColor: Optional[str] = Field(
        default="#E3F2FD",
        name="Background Color",
        description="Background color (hex format, e.g., #E3F2FD)",
    )


class GroupOutput(BaseModel):
    """Group node has no outputs - it's a visual container."""

    pass


class GroupNode(BaseNode):
    """A group node for organizing and grouping other nodes. Acts as a visual container."""

    input_schema = GroupInput
    output_schema = GroupOutput

    metadata = NodeMetadata(
        name="Group",
        description="A container for organizing multiple nodes together",
        category="utility",
        icon="📦",
        color="#E3F2FD",
        handles=NodeHandles(inputs=[], outputs=[]),  # No connection points
        skip_execution=True,  # Visual only, not executed
        display_component="group",  # Use custom group UI component
    )

    async def execute(
        self,
        inputs: dict[str, Any],
        context: NodeExecutionContext,
    ) -> GroupOutput:
        """Never called - group nodes skip execution."""
        return GroupOutput()
