"""Test node with multiple outputs for testing handle layout."""

import random
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


class MultiOutputTestInput(BaseModel):
    data: Any = Field(None, description="Input data (leave empty to use result from previous node)")


class MultiOutputTestOutput(BaseNodeOutput):
    """Output contains result and routing metadata."""

    result: Any = Field(..., description="Original input data (passthrough)")


class MultiOutputTestNode(BaseNode):
    """Test node with 7 outputs for testing handle layout and spacing."""

    input_schema = MultiOutputTestInput
    output_schema = MultiOutputTestOutput

    metadata = NodeMetadata(
        name="Multi Output Test",
        description="Test node with 7 outputs - generates random values on each output",
        category="testing",
        icon="🎲",
        color="#9C27B0",
        handles=NodeHandles(
            inputs=[HandleConfig(id="default", position="left")],
            outputs=[
                HandleConfig(id="output1", label="Out 1", position="right"),
                HandleConfig(id="output2", label="Out 2", position="right"),
                HandleConfig(id="output3", label="Out 3", position="right"),
                HandleConfig(
                    id="output4",
                    label="Out 4 with a longer label",
                    position="right",
                ),
                HandleConfig(id="output5", label="Out 5", position="right"),
                HandleConfig(id="output6", label="Out 6", position="right"),
                HandleConfig(id="output7", label="Out 7", position="right"),
            ],
            routing_mode="data_split",
        ),
    )

    async def execute_logic(
        self,
        validated_inputs: dict[str, Any],
        context: NodeExecutionContext,
    ) -> dict[str, Any]:
        """Generate random values on each output."""
        input_data = validated_inputs.get("data")

        # Return Pydantic instance with routing metadata
        # Generate random values for each output using outputs_data for data split routing
        return MultiOutputTestOutput(
            result=input_data,
            outputs_data={
                "output1": {
                    "value": random.randint(1, 100),
                    "source": "output1",
                    "input": input_data,
                },
                "output2": {
                    "value": random.randint(1, 100),
                    "source": "output2",
                    "input": input_data,
                },
                "output3": {
                    "value": random.randint(1, 100),
                    "source": "output3",
                    "input": input_data,
                },
                "output4": {
                    "value": random.randint(1, 100),
                    "source": "output4",
                    "input": input_data,
                },
                "output5": {
                    "value": random.randint(1, 100),
                    "source": "output5",
                    "input": input_data,
                },
                "output6": {
                    "value": random.randint(1, 100),
                    "source": "output6",
                    "input": input_data,
                },
                "output7": {
                    "value": random.randint(1, 100),
                    "source": "output7",
                    "input": input_data,
                },
            },
        )
