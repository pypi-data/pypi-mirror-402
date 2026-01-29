"""For Each loop node for processing lists.

NOTE: This node requires the runtime to implement the execute_subworkflow method
in the NodeExecutionContext. The flowire-app runtime provides this implementation.
"""

import asyncio
import logging
from typing import Any, Literal, Optional

from flowire_sdk import BaseNode, BaseNodeOutput, NodeExecutionContext, NodeMetadata
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ForEachInput(BaseModel):
    items: Optional[list[Any]] = Field(
        None,
        description=(
            "List of items to process. Use Insert button to reference data from other nodes. "
            "Must reference the field containing the array."
        ),
    )
    target_workflow_id: str = Field(..., description="Workflow ID containing the entry point to execute for each item")
    target_node_id: str = Field(
        ..., description="Entry point node ID to execute for each item (Workflow Trigger or Test Trigger)"
    )
    version: str = Field(
        "latest",
        description=(
            "Version to execute: 'default' (project's default tag), 'latest' (highest version), "
            "a tag slug like 'prod' or 'staging', or a specific version like 'v1', 'v2', etc."
        ),
    )
    execution_mode: Literal["inline", "distributed"] = Field(
        default="inline",
        description="Execution mode: 'inline' waits for results, 'distributed' fires tasks and returns immediately",
    )
    concurrency: int = Field(
        default=5, description="Maximum number of items to process in parallel (only used in inline mode)", ge=1, le=20
    )


class ForEachOutput(BaseNodeOutput):
    results: Optional[list[Any]] = Field(
        None, description="Array of results from successful subflow executions (only in inline mode)"
    )
    num_successes: int = Field(
        ..., description="Number of successful executions (inline) or dispatched executions (distributed)"
    )
    num_failures: int = Field(default=0, description="Number of failed executions (only in inline mode)")
    execution_ids: list[str] = Field(..., description="All child execution IDs")
    errors: list[dict[str, Any]] = Field(
        default_factory=list, description="Details of failed executions (only in inline mode)"
    )
    execution_mode: str = Field(..., description="Execution mode used: 'inline' or 'distributed'")


class ForEachNode(BaseNode):
    """Process each item in a list by executing a flow, with parallel execution support.

    This node delegates workflow execution to the runtime via context.execute_subworkflow().
    The runtime (flowire-app) handles:
    - Workflow resolution and version management
    - Celery task dispatch (for distributed mode)
    - Inline execution with concurrency control
    - Result collection
    """

    input_schema = ForEachInput
    output_schema = ForEachOutput

    metadata = NodeMetadata(
        name="For Each",
        description="Loop over a list and execute a flow for each item in parallel",
        category="logic",
        icon="🔁",
        color="#673AB7",
    )

    async def _execute_single_item(
        self,
        item: Any,
        item_index: int,
        workflow_id: str,
        trigger_node_id: str,
        version: str,
        context: NodeExecutionContext,
    ) -> dict[str, Any]:
        """Execute workflow for a single item."""
        try:
            result = await context.execute_subworkflow(
                workflow_id=workflow_id,
                trigger_data={
                    "target_node_id": trigger_node_id,
                    "call_data": item,
                    "version": version,
                    "item_index": item_index,
                },
                wait_for_completion=True,
            )

            if result is None:
                return {
                    "success": False,
                    "execution_id": None,
                    "item_index": item_index,
                    "error": "Sub-workflow returned no result",
                }

            execution_id = result.get("execution_id", "unknown")
            return_value = result.get("return_value")

            # Spread Return node data at top level, nest metadata under 'meta'
            if isinstance(return_value, dict):
                if "meta" in return_value:
                    raise ValueError(
                        f"Return node cannot use 'meta' as a key (item {item_index}). "
                        "This key is reserved for For Each execution metadata."
                    )
                structured_result = return_value.copy()
            elif return_value is not None:
                structured_result = {"value": return_value}
            else:
                structured_result = {}

            structured_result["meta"] = {
                "execution_id": execution_id,
                "item_index": item_index,
            }

            return {
                "success": True,
                "execution_id": execution_id,
                "item_index": item_index,
                "error": None,
                "result": structured_result,
            }

        except Exception as e:
            return {
                "success": False,
                "execution_id": None,
                "item_index": item_index,
                "error": str(e),
            }

    async def execute_logic(
        self,
        validated_inputs: dict[str, Any],
        context: NodeExecutionContext,
    ) -> dict[str, Any]:
        """Execute flow for each item in the list."""
        items = validated_inputs.get("items")
        if not items:
            raise ValueError(
                "Items list is required. Provide an 'items' array or reference a list field from a previous node."
            )

        if not isinstance(items, list):
            raise ValueError(f"Items must be a list, got {type(items).__name__}")

        target_workflow_id = validated_inputs.get("target_workflow_id")
        target_node_id = validated_inputs.get("target_node_id")
        version = validated_inputs.get("version", "latest")

        if not target_workflow_id or not target_node_id:
            raise ValueError("target_workflow_id and target_node_id are required")

        execution_mode = validated_inputs.get("execution_mode", "inline")
        concurrency = validated_inputs.get("concurrency", 5)

        # For distributed mode, use fire-and-forget via context
        if execution_mode == "distributed":
            execution_ids = []
            for idx, item in enumerate(items):
                try:
                    result = await context.execute_subworkflow(
                        workflow_id=target_workflow_id,
                        trigger_data={
                            "target_node_id": target_node_id,
                            "call_data": item,
                            "version": version,
                            "item_index": idx,
                        },
                        wait_for_completion=False,  # Fire and forget
                    )
                    if result and "execution_id" in result:
                        execution_ids.append(result["execution_id"])
                except Exception as e:
                    logger.warning(f"Failed to dispatch item {idx}: {e}")

            return ForEachOutput(
                results=None,
                num_successes=len(execution_ids),
                num_failures=0,
                execution_ids=execution_ids,
                errors=[],
                execution_mode="distributed",
            )

        # Inline mode: execute and wait for results with concurrency control
        successful_execution_ids = []
        successful_results = []
        all_execution_ids = []
        errors = []

        # Process items in batches based on concurrency limit
        total_items = len(items)
        for batch_start in range(0, total_items, concurrency):
            batch_end = min(batch_start + concurrency, total_items)
            batch = items[batch_start:batch_end]

            # Execute batch in parallel
            tasks = [
                self._execute_single_item(
                    item, batch_start + i, target_workflow_id, target_node_id, version, context
                )
                for i, item in enumerate(batch)
            ]

            batch_results = await asyncio.gather(*tasks, return_exceptions=False)

            # Collect execution IDs, results, and errors
            for item_result in batch_results:
                exec_id = item_result.get("execution_id")
                if exec_id:
                    all_execution_ids.append(exec_id)

                if item_result["success"]:
                    if exec_id:
                        successful_execution_ids.append(exec_id)
                    if "result" in item_result and item_result["result"] is not None:
                        successful_results.append(item_result["result"])
                else:
                    errors.append(
                        {
                            "item_index": item_result["item_index"],
                            "execution_id": exec_id,
                            "error": item_result["error"],
                        }
                    )

        # If all items failed, raise an error
        if errors and not successful_execution_ids:
            error_summary = f"All {len(errors)} items failed in For Each loop"
            if errors:
                first_error = errors[0]["error"]
                if len(first_error) > 200:
                    first_error = first_error[:200] + "..."
                error_summary += f". First error: {first_error}"
            raise ValueError(error_summary)

        return ForEachOutput(
            results=successful_results,
            num_successes=len(successful_execution_ids),
            num_failures=len(errors),
            execution_ids=all_execution_ids,
            errors=errors,
            execution_mode="inline",
        )
