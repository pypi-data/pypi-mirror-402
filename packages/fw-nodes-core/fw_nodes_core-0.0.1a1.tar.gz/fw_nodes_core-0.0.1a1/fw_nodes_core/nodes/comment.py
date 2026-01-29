"""Comment/Note node for flow documentation."""

from typing import Any

from flowire_sdk import BaseNode, NodeExecutionContext, NodeHandles, NodeMetadata
from pydantic import BaseModel, Field


class CommentInput(BaseModel):
    text: str = Field(
        default="", description="Comment text (supports markdown formatting)"
    )


class CommentOutput(BaseModel):
    pass


class CommentNode(BaseNode):
    """A comment/note node for documenting flows. Does not affect execution."""

    input_schema = CommentInput
    output_schema = CommentOutput

    metadata = NodeMetadata(
        name="Comment",
        description="Add notes and documentation to your flow",
        category="utility",
        icon="💬",
        color="#9E9E9E",
        handles=NodeHandles(inputs=[], outputs=[]),  # No connection points
        skip_execution=True,  # Visual only, not executed
        display_component="comment",  # Use custom comment UI component
    )

    async def execute(
        self,
        inputs: dict[str, Any],
        context: NodeExecutionContext,
    ) -> CommentOutput:
        """Never called - comment nodes skip execution."""
        return CommentOutput()
