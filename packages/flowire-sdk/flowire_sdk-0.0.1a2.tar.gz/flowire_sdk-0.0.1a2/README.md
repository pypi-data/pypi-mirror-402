# Flowire SDK

SDK for building Flowire workflow nodes.

## Installation

```bash
uv add flowire-sdk
```

For development:

```bash
uv add flowire-sdk --dev
```

## Quick Start

Create a custom node by extending `BaseNode`:

```python
from pydantic import BaseModel, Field
from flowire_sdk import BaseNode, BaseNodeOutput, NodeMetadata

# Define input schema
class GreetInput(BaseModel):
    name: str = Field(..., description="Name to greet")
    greeting: str = Field(default="Hello", description="Greeting to use")

# Define output schema (must extend BaseNodeOutput)
class GreetOutput(BaseNodeOutput):
    message: str = Field(..., description="The greeting message")

# Define the node
class GreetNode(BaseNode):
    input_schema = GreetInput
    output_schema = GreetOutput

    metadata = NodeMetadata(
        name="Greet",
        description="Generates a greeting message",
        category="utility",
        icon="👋",
    )

    async def execute_logic(self, validated_inputs, context):
        name = validated_inputs["name"]
        greeting = validated_inputs["greeting"]
        return GreetOutput(message=f"{greeting}, {name}!")
```

## Core Concepts

### BaseNode

The abstract base class all nodes inherit from. Provides:

- **Input/output validation** via Pydantic schemas
- **Expression parsing** for `{{node-id.field}}` references
- **Credential resolution** via execution context

### NodeMetadata

Configuration for node appearance and behavior:

```python
metadata = NodeMetadata(
    name="My Node",              # Display name in UI
    description="Does X",        # Tooltip description
    category="utility",          # Category for organization
    icon="🔧",                   # Emoji or icon name
    color="#4CAF50",            # UI color (optional)
    is_entry_point=False,       # Can start a workflow
    skip_execution=False,       # Visual-only node (e.g., comments)
)
```

### BaseNodeOutput

Base class for all node outputs. Supports routing:

```python
# Simple output (passthrough routing)
return MyOutput(result=data)

# Conditional routing (activates specific handle)
return MyOutput(result=data, output_handle="success")

# Data split routing (different data per handle)
return MyOutput(outputs_data={"path_a": data_a, "path_b": data_b})
```

### NodeExecutionContext

Abstract context provided during execution with access to:

- `workflow_id`, `execution_id`, `node_id`, `project_id`
- `node_results` - outputs from previous nodes
- `resolve_credential()` - decrypt stored credentials
- `resolve_project_variable()` - access project variables

### Credential Support

Nodes that need credentials define a credential schema:

```python
class MyCredentialSchema(BaseModel):
    api_key: str = Field(..., description="API key")

class MyNode(BaseNode):
    credential_schema = MyCredentialSchema

    async def execute_logic(self, validated_inputs, context):
        cred_id = validated_inputs.get("credential_id")
        if cred_id:
            creds = await context.resolve_credential(
                cred_id,
                self.get_credential_type()
            )
            api_key = creds["api_key"]
```

## Publishing Nodes

Package your nodes with entry points so Flowire auto-discovers them:

```toml
# pyproject.toml
[project.entry-points."flowire.nodes"]
my_node = "my_package.nodes:MyNode"
greet = "my_package.nodes:GreetNode"
```

See [fw-nodes-core](https://github.com/your-org/fw-nodes-core) for a complete example.

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

## API Reference

### Classes

| Class | Description |
|-------|-------------|
| `BaseNode` | Abstract base class for all nodes |
| `BaseNodeOutput` | Base class for node outputs with routing support |
| `NodeMetadata` | Node display and behavior configuration |
| `NodeExecutionContext` | Abstract execution context interface |
| `HandleConfig` | Configuration for connection handles |
| `NodeHandles` | Input/output handle definitions |

### BaseNode Methods

| Method | Description |
|--------|-------------|
| `execute(inputs, context)` | Main entry point (handles parsing/validation) |
| `execute_logic(validated_inputs, context)` | Override this for your logic |
| `get_input_schema()` | Returns input Pydantic model |
| `get_output_schema()` | Returns output Pydantic model |
| `get_metadata()` | Returns NodeMetadata |
| `resolve_expression(expr, context)` | Resolve a `{{...}}` expression |

## License

This project is licensed under the [MIT License](LICENSE).
