# Flowire Core Nodes

Core nodes for Flowire workflow automation. This package provides essential nodes for building workflows.

## Installation

```bash
uv add fw-nodes-core
```

Then add the package to your Flowire settings:

```python
# settings.py
installed_node_packages = ["fw-nodes-core"]
```

## Included Nodes

### Flow Control

| Node | Description |
|------|-------------|
| `WorkflowTrigger` | Entry point for workflows, receives trigger data |
| `Condition` | Conditional branching based on expressions |
| `ForEach` | Loop over arrays, executing sub-workflows |
| `CallFlow` | Execute another workflow as a sub-routine |
| `Delay` | Pause execution for a specified duration |
| `Return` | Return data from a workflow |

### Data Manipulation

| Node | Description |
|------|-------------|
| `SetValues` | Set or transform values with Jinja2 templates |
| `Strip` | Strip whitespace from strings |
| `GenerateJSONL` | Generate JSONL formatted output |
| `Debug` | Inspect data flowing through the pipeline |

### HTTP & Web

| Node | Description |
|------|-------------|
| `HTTPRequest` | Make HTTP requests (GET, POST, PUT, DELETE, etc.) |
| `HTMLParse` | Parse HTML with CSS/XPath selectors |
| `Webhook` | Receive external HTTP requests |
| `WebhookResponse` | Send response to webhook caller |

### Cloud Services

| Node | Description |
|------|-------------|
| `S3Upload` | Upload files to AWS S3 |

### Visual/Organization

| Node | Description |
|------|-------------|
| `Comment` | Add notes and documentation to workflows |
| `Group` | Visually group related nodes |

## Usage Examples

### HTTP Request

```python
# Node configuration in workflow:
{
    "method": "POST",
    "url": "https://api.example.com/data",
    "headers": {"Authorization": "Bearer {{project.api-key-uuid}}"},
    "body": {"name": "{{trigger.name}}"}
}
```

### Condition Node

```python
# Branch based on HTTP response status
{
    "condition": "{{http-request.status_code}} == 200"
}
# Outputs: "true" or "false" handles
```

### ForEach Loop

```python
# Process each item in an array
{
    "items": "{{http-request.data.results}}",
    "workflow_id": "process-item-workflow"
}
```

### HTMLParse

```python
# Extract data from HTML
{
    "html": "{{http-request.body}}",
    "selector": "div.product",
    "extract": "text"
}
```

## Creating Custom Nodes

Use this package as a reference for creating your own node packages:

1. **Create a new package** depending on `flowire-sdk`:

```toml
# pyproject.toml
[project]
name = "my-custom-nodes"
dependencies = ["flowire-sdk>=0.1.0"]

[project.entry-points."flowire.nodes"]
my_node = "my_custom_nodes.nodes:MyNode"
```

2. **Implement your node**:

```python
from pydantic import BaseModel, Field
from flowire_sdk import BaseNode, BaseNodeOutput, NodeMetadata

class MyInput(BaseModel):
    value: str = Field(..., description="Input value")

class MyOutput(BaseNodeOutput):
    result: str = Field(..., description="Processed result")

class MyNode(BaseNode):
    input_schema = MyInput
    output_schema = MyOutput
    metadata = NodeMetadata(
        name="My Node",
        description="Does something useful",
        category="custom",
    )

    async def execute_logic(self, validated_inputs, context):
        return MyOutput(result=f"Processed: {validated_inputs['value']}")
```

3. **Add to Flowire**:

```python
# settings.py
installed_node_packages = ["fw-nodes-core", "my-custom-nodes"]
```

## Development

```bash
# Install with dev dependencies
just install

# Run linter
just lint

# Auto-fix lint issues
just lint-fix

# Format code
just format

# Run tests
just test

# Run all checks
just check
```

## Testing Nodes

The test suite demonstrates how to test nodes in isolation using `MockExecutionContext`:

```python
import pytest
from fw_nodes_core.nodes.debug import DebugNode

@pytest.fixture
def node_execution_context():
    from tests.conftest import MockExecutionContext
    return MockExecutionContext(
        workflow_id="wf_123",
        execution_id="exec_456",
        node_id="node_789",
        project_id="proj_abc",
    )

@pytest.mark.asyncio
async def test_debug_node(node_execution_context):
    node = DebugNode()
    result = await node.execute(
        {"data": "test value"},
        node_execution_context
    )
    assert result.metadata["summary"]["type"] == "str"
```

## Project Structure

```
fw-nodes-core/
├── fw_nodes_core/
│   ├── __init__.py
│   └── nodes/
│       ├── __init__.py
│       ├── http_request.py
│       ├── condition.py
│       ├── debug.py
│       ├── delay.py
│       ├── set_values.py
│       ├── trigger.py
│       ├── call_flow.py
│       ├── for_each.py
│       ├── html_parse.py
│       ├── strip.py
│       ├── s3_upload.py
│       ├── comment.py
│       ├── group.py
│       ├── generate_jsonl.py
│       ├── return_node.py
│       ├── webhook.py
│       └── webhook_response.py
├── tests/
│   ├── conftest.py          # MockExecutionContext fixture
│   └── test_*.py            # Node tests
├── pyproject.toml
├── justfile
└── README.md
```

## License

This project is licensed under the [MIT License](LICENSE).
