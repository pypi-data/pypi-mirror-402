"""Schedule Trigger node for time-based workflow execution."""

from datetime import datetime
from datetime import timezone as tz
from typing import Any

from flowire_sdk import (
    BaseNode,
    BaseNodeOutput,
    HandleConfig,
    NodeExecutionContext,
    NodeHandles,
    NodeMetadata,
)
from pydantic import BaseModel, Field


class ScheduleTriggerInput(BaseModel):
    """Configuration for the schedule trigger."""

    cron_expression: str = Field(
        default="0 * * * *",
        description=(
            "Cron expression defining when to run. Format: minute hour day month weekday. "
            "See https://crontab.guru/ for help creating cron expressions."
        ),
    )
    timezone: str = Field(
        default="UTC",
        description="IANA timezone for schedule (e.g., 'America/New_York')",
    )


class ScheduleTriggerOutput(BaseNodeOutput):
    """Output containing schedule execution metadata."""

    scheduled_time: str = Field(
        ...,
        description="ISO8601 timestamp when execution was scheduled",
    )
    triggered_time: str = Field(
        ...,
        description="ISO8601 timestamp when execution actually started",
    )
    timezone: str = Field(
        ...,
        description="Timezone the schedule is configured for",
    )
    cron_expression: str = Field(
        ...,
        description="The effective cron expression",
    )
    next_scheduled_time: str | None = Field(
        default=None,
        description="ISO8601 timestamp of next scheduled execution",
    )


class ScheduleTriggerNode(BaseNode):
    """Triggers workflow execution on a cron schedule.

    This node acts as an entry point for workflows that should run on a schedule.
    Configure the schedule using a standard 5-field cron expression.

    See https://crontab.guru/ for help creating cron expressions.

    The schedule is managed by Redbeat (Redis-backed Celery Beat scheduler) and
    synced when the workflow is saved.
    """

    input_schema = ScheduleTriggerInput
    output_schema = ScheduleTriggerOutput

    metadata = NodeMetadata(
        name="Schedule Trigger",
        description=(
            "Triggers workflow execution on a cron schedule. "
            "See https://crontab.guru/ for help creating cron expressions."
        ),
        category="triggers",
        icon="🕐",
        color="#9C27B0",
        handles=NodeHandles(
            inputs=[],  # No inputs - entry point
            outputs=[HandleConfig(id="default", position="right")],
        ),
        is_entry_point=True,
        show_execute_button=True,  # Allow manual execution for testing
    )

    async def execute(
        self,
        inputs: dict[str, Any],
        context: NodeExecutionContext,
    ) -> ScheduleTriggerOutput:
        """Output schedule metadata.

        The trigger data is automatically added to inputs._trigger_data by the
        scheduler task when the schedule fires. For manual executions, we
        generate current timestamps.
        """
        # Get trigger data (injected by scheduler, may be absent for manual runs)
        trigger_data = inputs.get("_trigger_data", {})

        cron_expression = inputs.get("cron_expression", "0 * * * *")
        timezone = inputs.get("timezone", "UTC")
        now = datetime.now(tz.utc).isoformat()

        return ScheduleTriggerOutput(
            scheduled_time=trigger_data.get("scheduled_time", now),
            triggered_time=trigger_data.get("triggered_time", now),
            timezone=trigger_data.get("timezone", timezone),
            cron_expression=trigger_data.get("cron_expression", cron_expression),
            next_scheduled_time=trigger_data.get("next_scheduled_time"),
        )
