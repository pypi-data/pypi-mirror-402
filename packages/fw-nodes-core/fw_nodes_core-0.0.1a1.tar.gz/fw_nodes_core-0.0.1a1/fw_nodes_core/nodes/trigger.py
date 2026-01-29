"""Workflow Trigger node for marking entry points."""

from typing import Any

from flowire_sdk import BaseNode, BaseNodeOutput, HandleConfig, NodeExecutionContext, NodeHandles, NodeMetadata
from pydantic import BaseModel, Field


class WorkflowTriggerInput(BaseModel):
    pass


class WorkflowTriggerOutput(BaseNodeOutput):
    trigger_data: Any = Field(default=None, description="Data that triggered the workflow execution")


class WorkflowTriggerNode(BaseNode):
    """Entry point for workflows - receives trigger data and passes it through."""

    input_schema = WorkflowTriggerInput
    output_schema = WorkflowTriggerOutput

    metadata = NodeMetadata(
        name="Workflow Trigger",
        description="Entry point that receives trigger data when workflow is executed.",
        category="triggers",
        icon="▶️",
        color="#4CAF50",
        handles=NodeHandles(
            inputs=[],  # No inputs - entry point
            outputs=[HandleConfig(id="default", position="right")],
        ),
        is_entry_point=True,  # Can execute without incoming edges
        show_execute_button=True,  # Show inline execute button
    )

    async def execute(
        self,
        inputs: dict[str, Any],
        context: NodeExecutionContext,
    ) -> dict[str, Any]:
        """Pass through trigger data in trigger_data field.

        The trigger data is automatically added to inputs._trigger_data by the workflow executor
        for entry point nodes.
        """
        # Get trigger data from _trigger_data (added by WorkflowExecutor)
        # Default to None if not present to preserve the original data type
        trigger_data = inputs.get("_trigger_data")

        # Return trigger data in trigger_data field
        return WorkflowTriggerOutput(trigger_data=trigger_data)
