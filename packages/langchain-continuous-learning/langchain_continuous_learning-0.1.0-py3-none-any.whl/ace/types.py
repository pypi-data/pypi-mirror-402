"""Type definitions for ACE middleware.

These types provide the interface for the middleware framework. When used with
LangChain v1's built-in middleware system, these can be replaced with imports
from `langchain.agents.middleware.types`.
"""

from __future__ import annotations

from abc import ABC
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from langchain_core.messages import BaseMessage, SystemMessage
from typing_extensions import TypedDict

# Type variables for generic middleware
StateT = TypeVar("StateT", bound="AgentState")
ToolsT = TypeVar("ToolsT")


class AgentState(TypedDict, total=False):
    """Base agent state with messages.

    This is the minimal state schema required by agents. Middleware can
    extend this with additional fields.
    """

    messages: Sequence[BaseMessage]


@dataclass
class ModelRequest:
    """Request to the model.

    Attributes:
        state: Current agent state.
        system_message: System message/prompt for the model.
        messages: Conversation messages to send to the model.
    """

    state: AgentState
    system_message: SystemMessage | str | None
    messages: Sequence[BaseMessage]

    def override(
        self,
        *,
        system_message: SystemMessage | str | None = None,
        messages: Sequence[BaseMessage] | None = None,
    ) -> ModelRequest:
        """Create a new request with overridden fields.

        Args:
            system_message: New system message (if provided).
            messages: New messages (if provided).

        Returns:
            New ModelRequest with overridden fields.
        """
        return ModelRequest(
            state=self.state,
            system_message=system_message if system_message is not None else self.system_message,
            messages=messages if messages is not None else self.messages,
        )


@dataclass
class ModelResponse:
    """Response from the model.

    Attributes:
        message: The AI message response.
        raw_response: Raw response from the model (if available).
    """

    message: BaseMessage
    raw_response: Any = None


# Result type for model call wrappers
ModelCallResult = ModelResponse


class OmitFromSchema:
    """Marker for fields that should be omitted from the schema.

    Used to mark private state fields that shouldn't be exposed in
    input/output schemas.
    """

    def __init__(self, *, input: bool = True, output: bool = True) -> None:
        """Initialize OmitFromSchema marker.

        Args:
            input: Whether to omit from input schema.
            output: Whether to omit from output schema.
        """
        self.input = input
        self.output = output

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Allow use as annotation."""
        return self


# Placeholder for Runtime type from langgraph
class Runtime:
    """Placeholder for LangGraph runtime.

    In the actual LangChain v1 middleware system, this would be the
    LangGraph runtime that provides execution context.
    """

    pass


class AgentMiddleware(ABC, Generic[StateT, ToolsT]):
    """Base class for agent middleware.

    Middleware can intercept and modify agent behavior at various points:
    - before_agent: Called before agent execution starts
    - wrap_model_call: Wraps model invocations
    - after_model: Called after each model response

    Attributes:
        state_schema: Extended state schema for this middleware.
        tools: Additional tools registered by this middleware.
    """

    state_schema: type[AgentState] = AgentState
    tools: list[Any] = []

    def before_agent(self, state: StateT, runtime: Runtime) -> dict[str, Any] | None:
        """Called before agent execution starts.

        Args:
            state: Current agent state.
            runtime: LangGraph runtime.

        Returns:
            State updates to apply, or None.
        """
        return None

    async def abefore_agent(self, state: StateT, runtime: Runtime) -> dict[str, Any] | None:
        """Async version of before_agent.

        Args:
            state: Current agent state.
            runtime: LangGraph runtime.

        Returns:
            State updates to apply, or None.
        """
        return self.before_agent(state, runtime)

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelCallResult:
        """Wrap a model call.

        Args:
            request: The model request.
            handler: The next handler in the chain.

        Returns:
            The model response.
        """
        return handler(request)

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelCallResult:
        """Async version of wrap_model_call.

        Args:
            request: The model request.
            handler: The next handler in the chain.

        Returns:
            The model response.
        """
        return await handler(request)

    def after_model(self, state: StateT, runtime: Runtime) -> dict[str, Any] | None:
        """Called after each model response.

        Args:
            state: Current agent state.
            runtime: LangGraph runtime.

        Returns:
            State updates to apply, or None.
        """
        return None

    async def aafter_model(self, state: StateT, runtime: Runtime) -> dict[str, Any] | None:
        """Async version of after_model.

        Args:
            state: Current agent state.
            runtime: LangGraph runtime.

        Returns:
            State updates to apply, or None.
        """
        return self.after_model(state, runtime)
