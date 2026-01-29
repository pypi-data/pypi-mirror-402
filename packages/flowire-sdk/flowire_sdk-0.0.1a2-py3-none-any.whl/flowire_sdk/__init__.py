"""Flowire SDK - Base classes for building workflow nodes.

This package provides the core abstractions needed to build Flowire nodes:

- BaseNode: Abstract base class all nodes inherit from
- NodeMetadata: Configuration for node appearance and behavior
- NodeExecutionContext: Abstract context passed during execution
- BaseNodeOutput: Base class for node outputs with routing support
- HandleConfig: Configuration for connection handles
- NodeHandles: Input/output handle definitions

Example usage:

    from pydantic import BaseModel, Field
    from flowire_sdk import BaseNode, BaseNodeOutput, NodeMetadata

    class MyInput(BaseModel):
        message: str = Field(..., description="Input message")

    class MyOutput(BaseNodeOutput):
        result: str = Field(..., description="Processed result")

    class MyNode(BaseNode):
        input_schema = MyInput
        output_schema = MyOutput
        metadata = NodeMetadata(
            name="My Node",
            description="Processes a message",
            category="custom",
            icon="✨",
        )

        async def execute_logic(self, validated_inputs, context):
            return MyOutput(result=f"Processed: {validated_inputs['message']}")
"""

from flowire_sdk.node_base import (
    BaseNode,
    BaseNodeOutput,
    HandleConfig,
    NodeExecutionContext,
    NodeHandles,
    NodeMetadata,
)
from flowire_sdk.stream_handler import StreamHandler, StreamSubscription

__version__ = "0.1.0"

__all__ = [
    "BaseNode",
    "BaseNodeOutput",
    "HandleConfig",
    "NodeExecutionContext",
    "NodeHandles",
    "NodeMetadata",
    "StreamHandler",
    "StreamSubscription",
]
