"""Base classes for building Flowire workflow nodes.

This module provides the core abstractions that node developers need:
- BaseNode: Abstract base class all nodes inherit from
- NodeMetadata: Configuration for node appearance and behavior
- NodeExecutionContext: Abstract context passed during execution
- BaseNodeOutput: Base class for node outputs with routing support
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class HandleConfig(BaseModel):
    """Configuration for a single handle (input or output connection point)."""

    id: str = Field(..., description="Handle identifier (e.g., 'default', 'true', 'false')")
    label: Optional[str] = Field(None, description="Display label in UI")
    position: Literal["left", "right", "top", "bottom"] = Field(
        "right", description="Where to render the handle"
    )
    required: bool = Field(True, description="For inputs: must be connected for node to execute")
    style: Optional[dict[str, Any]] = Field(None, description="Custom CSS styles for the handle")


class NodeHandles(BaseModel):
    """Defines all input and output handles for a node."""

    inputs: list[HandleConfig] = Field(
        default_factory=lambda: [HandleConfig(id="default", position="left")],
        description="Input handles (connection points on the left)"
    )
    outputs: list[HandleConfig] = Field(
        default_factory=lambda: [HandleConfig(id="default", position="right")],
        description="Output handles (connection points on the right)"
    )
    routing_mode: Literal["passthrough", "conditional", "data_split"] = Field(
        default="passthrough",
        description=(
            "How data is routed to output handles:\n"
            "- passthrough: All outputs get same data (default)\n"
            "- conditional: Node returns _output field to indicate which handle activates\n"
            "- data_split: Node returns _outputs dict with different data per handle"
        )
    )


class NodeMetadata(BaseModel):
    """Metadata for a node type."""

    name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="What this node does")
    category: str = Field(default="general", description="Category for organization")
    icon: Optional[str] = Field(default=None, description="Icon name or emoji")
    color: Optional[str] = Field(default=None, description="Color for UI display")
    handles: Optional[NodeHandles] = Field(
        None,
        description="Handle configuration. If None, defaults to single input/output"
    )

    # Behavior flags for special node types
    is_entry_point: bool = Field(
        default=False,
        description="Can execute without incoming edges (e.g., FlowStart, Inject)"
    )
    skip_execution: bool = Field(
        default=False,
        description="Skip during execution (e.g., Comment, Group - visual only)"
    )
    display_component: Optional[str] = Field(
        default=None,
        description="Custom UI component for display: 'comment', 'group', or None for 'generic'"
    )
    show_execute_button: bool = Field(
        default=False,
        description="Show inline execute button in UI (for entry point nodes)"
    )
    is_webhook: bool = Field(
        default=False,
        description="Can be triggered via public /webhook/{id} endpoint. "
        "Use for webhook nodes that receive external HTTP requests (e.g., Webhook, SlackWebhook, GitHubWebhook)"
    )
    is_webhook_response: bool = Field(
        default=False,
        description="Publishes HTTP response back to webhook caller. "
        "When this node executes, its output is sent as the HTTP response to the waiting webhook endpoint. "
        "Only one webhook response node should execute per workflow."
    )
    store_unresolved_inputs: bool = Field(
        default=False,
        description="Store unresolved expression strings in execution results instead of resolved values"
    )
    is_stream_trigger: bool = Field(
        default=False,
        description="Requires persistent WebSocket connection via Connection Manager. "
        "When workflow contains this node and is enabled, Connection Manager establishes "
        "and maintains a connection to the external service."
    )
    stream_type: Optional[str] = Field(
        default=None,
        description="Stream handler type identifier (e.g., 'mattermost_ws', 'slack_rtm', 'discord_gateway'). "
        "Used by Connection Manager to select the appropriate handler implementation."
    )


class BaseNodeOutput(BaseModel):
    """Base class for all node outputs.

    Routing Metadata Fields:
    - output_handle: For conditional routing (routing_mode="conditional")
      Controls which output handle activates. Serializes as "_output".
      Example: output_handle="true" activates the "true" output handle.

    - outputs_data: For data split routing (routing_mode="data_split")
      Dictionary mapping handle IDs to their specific output data. Serializes as "_outputs".
      Example: outputs_data={"out1": {...}, "out2": {...}}

    Usage:
        # Conditional routing
        return MyOutput(result=data, output_handle="success")

        # Data split routing
        return MyOutput(result=data, outputs_data={"path_a": data_a, "path_b": data_b})

        # No routing (default passthrough)
        return MyOutput(result=data)
    """

    # Routing metadata fields (use field name in code, serializes with alias)
    output_handle: Optional[str] = Field(
        None,
        alias="_output",
        description="Which output handle to activate (conditional routing)"
    )
    outputs_data: Optional[dict[str, Any]] = Field(
        None,
        alias="_outputs",
        description="Data for each output handle (data split routing)"
    )

    model_config = ConfigDict(
        extra='forbid',  # Don't allow arbitrary fields - be explicit
        populate_by_name=True,  # Allow using either field name or alias
    )


class NodeExecutionContext(ABC):
    """Abstract context passed to node during execution.

    This is a protocol/interface that the runtime implements.
    Node developers code against this interface.

    Attributes:
        workflow_id: The ID of the workflow being executed
        execution_id: The ID of this specific execution
        node_id: The ID of the current node
        project_id: The ID of the project
        user_id: The ID of the user (None for webhook-triggered flows)
        node_results: Dictionary of previous node outputs keyed by node ID
    """

    workflow_id: str
    execution_id: str
    node_id: str
    project_id: str
    user_id: Optional[str]
    node_results: dict[str, dict[str, Any]]

    @abstractmethod
    async def resolve_credential(self, credential_id: str, credential_type: str) -> dict:
        """Resolve and decrypt credential for use in node execution.

        Performs security checks:
        1. Credential exists and belongs to project
        2. Credential type matches what node expects
        3. Workflow has access to credential
        4. Decrypts and validates against current schema

        Args:
            credential_id: UUID of the credential
            credential_type: Expected credential type (e.g., 's3')

        Returns:
            Decrypted credential data as dict

        Raises:
            ValueError: If credential not found or type mismatch
            PermissionError: If workflow doesn't have access
        """
        pass

    @abstractmethod
    async def resolve_project_variable(self, key: str) -> Any:
        """Resolve project variable value by key.

        Args:
            key: Project variable key (e.g., 'aws.bucket_name')

        Returns:
            Project variable value (decrypted if secret)

        Raises:
            ValueError: If project variable not found
            PermissionError: If workflow doesn't have access
        """
        pass

    @abstractmethod
    async def resolve_project_variable_by_id(self, variable_id: str) -> Any:
        """Resolve project variable value by ID (instead of key).

        Args:
            variable_id: Project variable UUID

        Returns:
            Project variable value (decrypted if secret)

        Raises:
            ValueError: If variable not found
            PermissionError: If workflow doesn't have access
        """
        pass

    @abstractmethod
    def register_secret(self, value: str) -> None:
        """Register a secret value for automatic redaction."""
        pass

    @abstractmethod
    def get_secrets(self) -> set:
        """Get all registered secret values for redaction."""
        pass

    def get_redacted_logger(self, name: str) -> logging.Logger:
        """Get a logger that automatically redacts secrets.

        Default implementation returns a standard logger.
        Runtime can override to provide redaction.

        Args:
            name: Logger name (usually __name__)

        Returns:
            Logger instance
        """
        return logging.getLogger(name)

    def redact_data(self, data: Any) -> Any:
        """Redact all registered secrets from a data structure.

        Default implementation returns data unchanged.
        Runtime can override to provide redaction.

        Args:
            data: Data structure to redact

        Returns:
            Redacted copy of the data
        """
        return data

    def publish_webhook_error(self, error: str, status_code: int = 500) -> None:  # noqa: B027
        """Publish an error response for webhook-triggered workflows.

        Default implementation does nothing.
        Runtime can override to publish errors.

        Args:
            error: Error message to return to the caller
            status_code: HTTP status code (default 500)
        """
        pass

    def publish_immediate_response(  # noqa: B027
        self,
        status_code: int = 200,
        body: Any = None,
        content_type: str = "application/json",
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        """Publish an immediate response for webhook-triggered workflows.

        Call this to send a response immediately without waiting for the
        workflow to complete. Useful for webhooks that don't need a response
        (e.g., Mattermost outgoing webhooks).

        Default implementation does nothing.
        Runtime can override to publish responses.

        Args:
            status_code: HTTP status code (default 200)
            body: Response body (default None for empty response)
            content_type: Content-Type header (default application/json)
            headers: Additional response headers
        """
        pass

    async def execute_subworkflow(
        self,
        workflow_id: str,
        trigger_data: dict[str, Any],
        wait_for_completion: bool = True,
    ) -> Optional[dict[str, Any]]:
        """Execute a sub-workflow (for CallFlow/ForEach nodes).

        Default implementation raises NotImplementedError.
        Runtime provides actual implementation.

        Args:
            workflow_id: ID of the workflow to execute
            trigger_data: Data to pass to the workflow trigger
            wait_for_completion: If True, wait for result; if False, fire and forget

        Returns:
            Workflow result if wait_for_completion=True, else None

        Raises:
            NotImplementedError: If runtime doesn't support sub-workflows
        """
        raise NotImplementedError("Sub-workflow execution not available in this context")

    def store_binary(
        self,
        data: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Store binary data and return a storage reference.

        Default implementation raises NotImplementedError.
        Runtime provides actual storage implementation (S3, local, etc.).

        Args:
            data: Binary data to store
            filename: Filename for the stored data
            content_type: MIME type of the data
            metadata: Optional metadata to store with the file

        Returns:
            Storage reference dict that can be used to retrieve the data

        Raises:
            NotImplementedError: If runtime doesn't support storage
        """
        raise NotImplementedError("Binary storage not available in this context")


class BaseNode(ABC):
    """Base class for all nodes in the flow system.

    Nodes can define schemas and metadata in two ways:

    1. Class attributes (recommended - less boilerplate):
        class MyNode(BaseNode):
            input_schema = MyInput
            output_schema = MyOutput
            metadata = NodeMetadata(...)
            credential_schema = MyCredential  # optional
            credential_type = "my_type"       # optional

    2. Class methods (legacy - still supported):
        Override get_input_schema(), get_output_schema(), get_metadata()

    Each node must implement execute() method.
    """

    # Class attributes - subclasses can set these instead of overriding methods
    input_schema: Optional[type[BaseModel]] = None
    output_schema: Optional[type[BaseModel]] = None
    metadata: Optional[NodeMetadata] = None
    credential_schema: Optional[type[BaseModel]] = None
    credential_type: Optional[str] = None

    @classmethod
    def get_node_id(cls) -> str:
        """Return the unique node ID auto-derived from the class path.

        Returns:
            Fully qualified class name (e.g., 'app.nodes.http_request.HttpRequestNode')
        """
        return f"{cls.__module__}.{cls.__name__}"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        """Return metadata about this node type.

        Can be overridden for dynamic metadata, or set metadata class attribute.
        """
        if cls.metadata is None:
            raise NotImplementedError(
                f"{cls.__name__} must define 'metadata' class attribute or override get_metadata()"
            )
        return cls.metadata

    @classmethod
    def get_input_schema(cls) -> type[BaseModel]:
        """Return Pydantic model for input validation.

        Can be overridden for dynamic schema, or set input_schema class attribute.
        """
        if cls.input_schema is None:
            raise NotImplementedError(
                f"{cls.__name__} must define 'input_schema' class attribute or override get_input_schema()"
            )
        return cls.input_schema

    @classmethod
    def get_output_schema(cls) -> type[BaseModel]:
        """Return Pydantic model for output validation.

        Can be overridden for dynamic schema, or set output_schema class attribute.
        """
        if cls.output_schema is None:
            raise NotImplementedError(
                f"{cls.__name__} must define 'output_schema' class attribute or override get_output_schema()"
            )
        return cls.output_schema

    @classmethod
    def get_credential_schema(cls) -> Optional[type[BaseModel]]:
        """Return Pydantic model for credential data (optional).

        Can be overridden for dynamic schema, or set credential_schema class attribute.
        Returns None if node doesn't need credentials.
        """
        return cls.credential_schema

    @classmethod
    def get_credential_type(cls) -> Optional[str]:
        """Return the credential type identifier (optional).

        Auto-derives from credential_schema's fully qualified class name.
        Nodes can explicitly set credential_type to override (rare).

        Returns:
            Fully qualified class name (e.g., "app.nodes.s3_upload.S3CredentialSchema")
            or None if no credentials needed.
        """
        # Explicit override takes precedence (escape hatch)
        if cls.credential_type is not None:
            return cls.credential_type

        # Auto-derive from credential_schema
        if cls.credential_schema is not None:
            schema_class = cls.credential_schema
            return f"{schema_class.__module__}.{schema_class.__name__}"

        return None

    async def execute(
        self,
        inputs: dict[str, Any],
        context: NodeExecutionContext,
    ) -> Union[BaseModel, dict[str, Any]]:
        """Execute node with standard preprocessing pipeline.

        This method provides a default implementation that handles:
        1. Expression parsing (resolves {{...}} expressions)
        2. Input validation (against schema)

        Most nodes should implement execute_logic() instead of overriding this method.
        Only override this method if you need custom preprocessing logic.

        Args:
            inputs: Input data as dict (will be validated against input_schema)
            context: Execution context with flow_id, execution_id, node_id

        Returns:
            Output data as Pydantic model instance or dict.
            - Most nodes: Return Pydantic instance (defined by get_output_schema)
            - Nodes with routing: Return dict with routing metadata (_output or _outputs)
            The executor will serialize Pydantic instances to dicts automatically.
        """
        # Standard preprocessing pipeline
        await self.parse_expressions_in_schema_fields(inputs, context)
        validated_inputs = self.validate_inputs(inputs)

        # Call node-specific business logic
        return await self.execute_logic(validated_inputs, context)

    async def execute_logic(
        self,
        validated_inputs: dict[str, Any],
        context: NodeExecutionContext,
    ) -> Union[BaseModel, dict[str, Any]]:
        """Execute node business logic with pre-validated inputs.

        Override this method to implement your node's core functionality.

        Inputs have already been:
        - Expression-parsed ({{...}} resolved)
        - Field-mapped (result.field -> field)
        - Validated against input schema

        If your node needs custom preprocessing (e.g., selective expression parsing),
        override execute() instead of this method (and skip implementing execute_logic).

        Args:
            validated_inputs: Pre-validated input data (guaranteed to match input_schema)
            context: Execution context with flow_id, execution_id, node_id

        Returns:
            Output data as Pydantic model instance or dict.
            - Most nodes: Return Pydantic instance (defined by get_output_schema)
            - Nodes with routing: Return dict with routing metadata (_output or _outputs)
            The executor will serialize Pydantic instances to dicts automatically.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement execute_logic() or override execute()"
        )

    def validate_inputs(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Validate inputs against schema."""
        schema = self.get_input_schema()
        validated = schema(**inputs)
        return validated.model_dump()

    async def resolve_expression(
        self,
        expression: str,
        context: NodeExecutionContext
    ) -> Any:
        """Resolve a single expression (without curly braces).

        Supports: node-id.field, project.variable-uuid, or _meta.field

        Args:
            expression: Expression to resolve
            context: Execution context

        Returns:
            The resolved value

        Raises:
            ValueError: If reference not found
        """
        parts = expression.split(".")
        root = parts[0]
        path = parts[1:] if len(parts) > 1 else []

        # Pattern 1: Project variable access
        if root == "project":
            if not path:
                raise ValueError("project reference requires a variable ID (e.g., project.abc-123-uuid)")
            variable_id = path[0]  # First part after "project." is the UUID
            return await context.resolve_project_variable_by_id(variable_id)

        # Pattern 2: Global execution metadata access
        if root == "_meta":
            # Build global _meta dict from execution context
            meta_dict = {
                "execution_id": context.execution_id,
                "flow_id": context.workflow_id,
                "node_id": context.node_id,  # Current node being executed
                "project_id": context.project_id,
            }

            if not path:
                # Return entire _meta dict
                return meta_dict

            # Navigate nested path in _meta
            current = meta_dict
            for i, part in enumerate(path):
                current = self._navigate_path(current, part, "_meta", path[:i])

            return current

        # Pattern 3: Node output access (by node ID)
        if root in context.node_results:
            current = context.node_results[root]

            # Navigate nested path
            for i, part in enumerate(path):
                current = self._navigate_path(current, part, root, path[:i])

            return current

        # Not found - show helpful error
        available_nodes = list(context.node_results.keys())
        raise ValueError(
            f"Node reference '{root}' not found. Available nodes: {', '.join(available_nodes)}"
        )

    def _navigate_path(
        self,
        current: Any,
        part: str,
        root: str,
        path_so_far: list[str] = None
    ) -> Any:
        """Navigate a single step in a dotted path.

        Args:
            current: Current value to navigate into
            part: Path segment to access (field name or array index)
            root: Root reference name (for error messages)
            path_so_far: Path traversed so far (for error messages)

        Returns:
            Value at the path

        Raises:
            ValueError: If path cannot be navigated
        """
        if path_so_far is None:
            path_so_far = []

        if isinstance(current, dict):
            if part not in current:
                raise ValueError(
                    f"Field '{part}' not found in {root}. "
                    f"Available fields: {', '.join(current.keys())}"
                )
            return current[part]
        elif isinstance(current, list):
            try:
                index = int(part)
                if index < 0 or index >= len(current):
                    raise ValueError(
                        f"Index {index} out of range. "
                        f"Array has {len(current)} elements."
                    )
                return current[index]
            except ValueError as err:
                raise ValueError(
                    f"Invalid array index '{part}' in expression"
                ) from err
        else:
            full_path = ".".join([root] + path_so_far)
            raise ValueError(
                f"Cannot access '{part}' on {type(current).__name__} "
                f"at path '{full_path}'"
            )

    async def parse_expressions(
        self,
        value: Any,
        context: NodeExecutionContext
    ) -> Any:
        """Parse all expressions in a value before validation.

        This recursively processes the value, resolving any expressions
        found in string values.

        Args:
            value: The value to parse (dict, list, string, or any type)
            context: Execution context with node_results

        Returns:
            New value with expressions resolved (same type as input)
        """
        return await self._parse_value(value, context)

    async def parse_expressions_in_schema_fields(
        self,
        inputs: dict[str, Any],
        context: NodeExecutionContext
    ) -> dict[str, Any]:
        """Parse expressions only in fields defined in the input schema.

        This avoids parsing expressions in passthrough data fields like 'result',
        'initial_data', '_meta' which may contain user data with curly braces
        (e.g., HTML with JavaScript, JSON strings, etc.)

        Args:
            inputs: Node inputs dict
            context: Execution context

        Returns:
            Inputs dict with expressions parsed in schema fields only
        """
        schema = self.get_input_schema()
        schema_fields = set(schema.model_fields.keys())

        # Parse expressions only in fields that are defined in the schema
        for field_name in schema_fields:
            if field_name in inputs:
                inputs[field_name] = await self.parse_expressions(inputs[field_name], context)

        return inputs

    async def _parse_value(
        self,
        value: Any,
        context: NodeExecutionContext
    ) -> Any:
        """Recursively parse expressions in a value."""
        if isinstance(value, str):
            # Check for pure expression (entire string is single expression)
            # Must start/end with double braces, have exactly one opening double brace, and not look like JSON
            if value.startswith("{{") and value.endswith("}}") and value.count("{{") == 1:
                inner = value[2:-2].strip()
                # Skip if inner is empty (e.g., '{}' is empty JSON, not an expression)
                if not inner:
                    return value
                # Skip JSON-like content (has quotes and colons)
                # Valid expressions: node-id.field, project.uuid, _meta.field
                if not ('"' in inner and ':' in inner) and not ("'" in inner and ':' in inner):
                    result = await self.resolve_expression(inner, context)
                    return result

            # Check for template string (contains expressions)
            if "{{" in value:
                import re
                # Pattern that matches {{expression}} but NOT JSON like {"key": "value"}
                # Expressions should start with a word character (letter, digit, underscore)
                # not with a quote
                pattern = r'\{\{([A-Za-z_][^}]*)\}\}'
                matches = list(re.finditer(pattern, value))

                # Resolve all expressions asynchronously
                replacements = []
                for match in matches:
                    expr = match.group(1)
                    # Skip if this looks like JSON (contains : and ")
                    if '"' in expr and ':' in expr:
                        replacements.append((match.group(0), match.group(0)))  # No change
                        continue

                    result = await self.resolve_expression(expr, context)
                    # Convert to string for interpolation
                    if isinstance(result, (dict, list)):
                        import json
                        result_str = json.dumps(result)
                    else:
                        result_str = str(result)

                    replacements.append((match.group(0), result_str))

                # Apply all replacements
                for old, new in replacements:
                    value = value.replace(old, new, 1)

                return value

            # No expressions
            return value

        elif isinstance(value, dict):
            return {k: await self._parse_value(v, context) for k, v in value.items()}

        elif isinstance(value, list):
            return [await self._parse_value(item, context) for item in value]

        else:
            # Primitive type
            return value
