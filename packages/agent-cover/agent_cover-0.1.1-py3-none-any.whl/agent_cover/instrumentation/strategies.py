"""Defines wrapper strategies for agent execution context management.

This module provides abstract and concrete implementations of wrapper strategies
used to intercept method calls. These strategies are primarily responsible for
managing the execution context (activating and resetting tokens) during
synchronous, asynchronous, and generator executions within the agent coverage
framework.
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any, AsyncIterator, Callable

from agent_cover.context import (
    AgentContextManager,  # Importing the AgentContextManager for managing execution context
)

logger = logging.getLogger(__name__)


class WrapperStrategy(ABC):
    """Abstract base strategy for method interception.

    This interface implements the **Strategy Pattern**. It allows the instrumentor
    to decide *what* to do when a method is called, decoupling it from *how* to
    patch the method.
    """

    @abstractmethod
    def wrap(self, original: Any, context: Any) -> Any:
        """Wraps a method or class.

        Args:
            original: The original method or class to be wrapped.
            context: A context object (can contain registry, context_manager, etc.).

        Returns:
            Any: The wrapped method or class.
        """
        pass


# --- GENERIC STRATEGIES (Sync/Async execution context) ---


class BaseExecutionStrategy(WrapperStrategy):
    """Base class for strategies that require the ContextManager.

    Attributes:
        None

    Methods:
        wrap: Inherited from WrapperStrategy.
    """

    pass


class SyncContextWrapper(BaseExecutionStrategy):
    """Strategy for wrapping synchronous methods to manage the agent context.

    Attributes:
        None

    Methods:
        wrap: Wraps a synchronous callable to handle context activation/deactivation.
    """

    def wrap(self, original: Callable, ctx_manager: AgentContextManager) -> Callable:
        """Wraps a synchronous method to activate and deactivate the agent context.

        Args:
            original: The original synchronous method.
            ctx_manager: The AgentContextManager used to manage the execution context.

        Returns:
            Callable: A wrapper function that manages the agent context around the original call.
        """

        def wrapper(instance: Any, *args: Any, **kwargs: Any) -> Any:
            """The wrapper function handling the context lifecycle."""
            token = ctx_manager.set_active(True)  # Activate the agent context
            try:
                return original(
                    instance, *args, **kwargs
                )  # Execute the original method
            finally:
                ctx_manager.reset(token)  # Reset the agent context

        return wrapper


class AsyncContextWrapper(BaseExecutionStrategy):
    """Wraps asynchronous methods (coroutines) to maintain Agent context.

    This is critical for frameworks like LangChain where execution jumps between
    threads and event loops. It ensures that the `contextvars` token is set
    correctly before `await`ing the original coroutine and reset immediately after.

    Args:
        original: The original `async def` function.
        ctx_manager: The manager handling the context token.

    Returns:
        Callable: An async wrapper that maintains scope.
    """

    def wrap(self, original: Callable, ctx_manager: AgentContextManager) -> Callable:
        """Wraps an asynchronous method to activate and deactivate the agent context.

        Args:
            original: The original asynchronous method.
            ctx_manager: The AgentContextManager used to manage the execution context.

        Returns:
            Callable: An asynchronous wrapper function that manages the agent context.
        """

        async def wrapper(instance: Any, *args: Any, **kwargs: Any) -> Any:
            """The asynchronous wrapper function handling the context lifecycle."""
            token = ctx_manager.set_active(True)  # Activate the agent context
            try:
                return await original(
                    instance, *args, **kwargs
                )  # Execute the original method
            finally:
                ctx_manager.reset(token)  # Reset the agent context

        return wrapper


class SyncGenContextWrapper(BaseExecutionStrategy):
    """Wraps synchronous generators (functions using `yield`).

    Generators are tricky because execution pauses and resumes. This wrapper
    ensures the Agent context is active *every time* the generator executes code,
    but inactive when it yields control back to the caller.
    """

    def wrap(self, original: Callable, ctx_manager: AgentContextManager) -> Callable:
        """Wraps a synchronous generator method.

        We cannot use `yield from` inside a `try/finally` because that keeps
        the context active while the generator is suspended. We must iterate manually.
        """

        def wrapper(instance: Any, *args: Any, **kwargs: Any) -> Iterator[Any]:
            iterator = original(instance, *args, **kwargs)
            while True:
                token = ctx_manager.set_active(True)
                try:
                    value = next(iterator)
                except StopIteration:
                    ctx_manager.reset(token)
                    return
                except Exception as e:
                    logger.warning(e, exc_info=True)
                    ctx_manager.reset(token)
                    raise

                # Reset BEFORE yielding to caller
                ctx_manager.reset(token)
                yield value

        return wrapper


class AsyncGenContextWrapper(BaseExecutionStrategy):
    """Strategy for wrapping asynchronous generator methods to manage the agent context.

    Similar to the sync generator, we must ensure context is active only during
    the `await` / processing phases inside the generator, and closed during yield.
    """

    def wrap(self, original: Callable, ctx_manager: AgentContextManager) -> Callable:
        """Wraps an asynchronous generator method.

        Manually iterates using `__anext__` to control context boundaries.
        """

        async def wrapper(
            instance: Any, *args: Any, **kwargs: Any
        ) -> AsyncIterator[Any]:
            iterator = original(instance, *args, **kwargs)
            while True:
                token = ctx_manager.set_active(True)
                try:
                    # Use manual iteration protocol for async generators
                    value = await iterator.__anext__()
                except StopAsyncIteration:
                    ctx_manager.reset(token)
                    return
                except Exception as e:
                    logger.warning(e, exc_info=True)
                    ctx_manager.reset(token)
                    raise

                # Reset BEFORE yielding to caller
                ctx_manager.reset(token)
                yield value

        return wrapper
