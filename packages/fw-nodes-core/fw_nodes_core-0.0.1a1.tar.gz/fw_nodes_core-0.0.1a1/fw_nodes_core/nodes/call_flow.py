"""Call flow execution node for workflow orchestration.

NOTE: This node requires the runtime to implement the execute_subworkflow method
in the NodeExecutionContext. The flowire-app runtime provides this implementation.
"""

import logging
from typing import Any

from flowire_sdk import BaseNode, BaseNodeOutput, NodeExecutionContext, NodeMetadata
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class CallFlowInput(BaseModel):
    target_workflow_id: str = Field(..., description="Workflow containing the entry point to call")
    target_node_id: str = Field(..., description="Entry point node to call (Workflow Trigger or Test Trigger)")
    call_data: Any = Field(
        None, description="Data to pass to the called workflow. Use Insert button to reference data from other nodes."
    )
    version: str = Field(
        "latest",
        description=(
            "Version to execute: 'default' (project's default tag), 'latest' (highest version), "
            "a tag slug like 'prod' or 'staging', or a specific version like 'v1', 'v2', etc."
        ),
    )


class CallFlowOutput(BaseNodeOutput):
    meta: dict[str, Any] = Field(..., description="Call Flow execution metadata")

    class Config:
        extra = "allow"  # Allow Return node fields at top level


class CallFlowNode(BaseNode):
    """Call another workflow and wait for its result (like a function call).

    This node delegates workflow execution to the runtime via context.execute_subworkflow().
    The runtime (flowire-app) handles:
    - Workflow resolution and version management
    - Rate limiting
    - Celery task dispatch
    - Polling for completion
    - Result extraction
    """

    # Timeout configuration (can be overridden for testing)
    max_wait_seconds: float = 300  # 5 minute timeout

    input_schema = CallFlowInput
    output_schema = CallFlowOutput

    metadata = NodeMetadata(
        name="Call Flow",
        description="Call another workflow and wait for its result",
        category="logic",
        icon="📞",
        color="#9C27B0",
    )

    async def execute_logic(
        self,
        validated_inputs: dict[str, Any],
        context: NodeExecutionContext,
    ) -> dict[str, Any]:
        """Call a workflow and wait for its completion."""
        target_workflow_id = validated_inputs.get("target_workflow_id")
        target_node_id = validated_inputs.get("target_node_id")
        call_data = validated_inputs.get("call_data")
        version = validated_inputs.get("version", "latest")

        if not target_workflow_id or not target_node_id:
            raise ValueError("target_workflow_id and target_node_id are required")

        # Delegate to runtime via context
        result = await context.execute_subworkflow(
            workflow_id=target_workflow_id,
            trigger_data={
                "target_node_id": target_node_id,
                "call_data": call_data,
                "version": version,
                "max_wait_seconds": self.max_wait_seconds,
            },
            wait_for_completion=True,
        )

        if result is None:
            raise ValueError("Sub-workflow execution returned no result")

        # Extract return value from execution result
        return_value = result.get("return_value")
        execution_id = result.get("execution_id", "unknown")
        execution_time_ms = result.get("execution_time_ms", 0)

        # Spread Return node data at top level, nest metadata under 'meta'
        if isinstance(return_value, dict):
            if "meta" in return_value:
                raise ValueError(
                    "Return node cannot use 'meta' as a key. "
                    "This key is reserved for Call Flow execution metadata."
                )
            output_dict = return_value.copy()
        elif return_value is not None:
            # Non-dict, non-None values (primitives, lists) go under 'value' key
            output_dict = {"value": return_value}
        else:
            # None return value - no data to spread, only metadata
            output_dict = {}

        # Add metadata under 'meta'
        output_dict["meta"] = {
            "execution_id": execution_id,
            "workflow_id": target_workflow_id,
            "triggered": True,
            "execution_time_ms": execution_time_ms,
        }

        return CallFlowOutput(**output_dict)
