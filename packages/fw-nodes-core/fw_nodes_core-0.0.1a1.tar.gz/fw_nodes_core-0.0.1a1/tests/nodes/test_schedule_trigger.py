"""Tests for Schedule Trigger node."""

import pytest

from fw_nodes_core.nodes.schedule_trigger import (
    ScheduleTriggerInput,
    ScheduleTriggerNode,
)


@pytest.fixture
def schedule_trigger_node():
    return ScheduleTriggerNode()


@pytest.fixture
def sample_schedule_trigger_data():
    """Sample trigger data that would be injected by the scheduler."""
    return {
        "scheduled_time": "2026-01-18T09:00:00-05:00",
        "triggered_time": "2026-01-18T09:00:01-05:00",
        "timezone": "America/New_York",
        "cron_expression": "0 9 * * 1-5",
        "next_scheduled_time": "2026-01-19T09:00:00-05:00",
    }


class TestScheduleTriggerNode:
    """Tests for ScheduleTriggerNode."""

    def test_node_metadata(self, schedule_trigger_node):
        """Test node has correct metadata."""
        metadata = schedule_trigger_node.get_metadata()

        assert metadata.name == "Schedule Trigger"
        assert metadata.category == "triggers"
        assert metadata.is_entry_point is True
        assert len(metadata.handles.inputs) == 0  # Entry point has no inputs
        assert "crontab.guru" in metadata.description

    def test_input_schema_defaults(self):
        """Test input schema has sensible defaults."""
        inputs = ScheduleTriggerInput()

        assert inputs.cron_expression == "0 * * * *"
        assert inputs.timezone == "UTC"

    def test_input_schema_cron_expression(self):
        """Test input schema accepts cron expression."""
        inputs = ScheduleTriggerInput(
            cron_expression="0 9 * * 1-5",
            timezone="America/New_York",
        )

        assert inputs.cron_expression == "0 9 * * 1-5"
        assert inputs.timezone == "America/New_York"

    @pytest.mark.asyncio
    async def test_execute_outputs_schedule_metadata(
        self,
        schedule_trigger_node,
        node_execution_context,
        sample_schedule_trigger_data,
    ):
        """Test node outputs schedule metadata from trigger data."""
        inputs = {
            "cron_expression": "0 9 * * 1-5",
            "timezone": "America/New_York",
            "_trigger_data": sample_schedule_trigger_data,
        }

        result = await schedule_trigger_node.execute(inputs, node_execution_context)
        result_dict = result.model_dump(exclude_none=True, by_alias=True)

        assert result_dict["scheduled_time"] == "2026-01-18T09:00:00-05:00"
        assert result_dict["triggered_time"] == "2026-01-18T09:00:01-05:00"
        assert result_dict["timezone"] == "America/New_York"
        assert result_dict["cron_expression"] == "0 9 * * 1-5"
        assert result_dict["next_scheduled_time"] == "2026-01-19T09:00:00-05:00"

    @pytest.mark.asyncio
    async def test_execute_without_trigger_data_uses_defaults(
        self,
        schedule_trigger_node,
        node_execution_context,
    ):
        """Test node handles missing trigger data gracefully (manual execution)."""
        inputs = {
            "cron_expression": "0 9 * * 1-5",
            "timezone": "America/New_York",
        }

        result = await schedule_trigger_node.execute(inputs, node_execution_context)
        result_dict = result.model_dump(exclude_none=True, by_alias=True)

        # Should still have timezone and cron from inputs
        assert result_dict["timezone"] == "America/New_York"
        assert result_dict["cron_expression"] == "0 9 * * 1-5"
        # Times should be populated (current time for manual execution)
        assert "triggered_time" in result_dict
