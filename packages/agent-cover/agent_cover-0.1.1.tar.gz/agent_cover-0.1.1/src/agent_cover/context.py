"""Context management utilities for tracking Agent execution scope.

This module provides the mechanism to distinguish between:
1.  **Test Logic**: Code running in your test function (setup, assertions).
2.  **Agent Logic**: Code running inside the agent's execution loop.

It utilizes `contextvars` to ensure async-safety. This means even if multiple
agents run in parallel (e.g., `pytest-xdist` or `asyncio.gather`), the
coverage tracking remains isolated and accurate for each execution flow.

## 🔗 Architectural Relationships

To ensure accurate coverage metrics without false positives, different instrumentation
components interact with this manager in specific ways:

### 1. Scope Providers (The Activators)
* **[Agents][agent_cover.instrumentation.agents]:** These components act as the entry point.
    They call `set_active(True)` to signal that the "Agent Logic" loop has started.

### 2. Scope Consumers (The Gatekeepers)
* **[Tools][agent_cover.instrumentation.tools] & [Prompts][agent_cover.instrumentation.prompts]:**
    These objects are ambiguous—they can be executed by the agent *or* manually by your test setup code (e.g., formatting a prompt to assert against a string).
* **Behavior:** They explicitly **check** this manager. If `is_active()` returns `False`, they ignore the execution to prevent polluting the coverage report with test setup data.

### 3. Context-Agnostic Components (The Bypassers)
* **[LLM Providers][agent_cover.instrumentation.llm_providers], [Callbacks][agent_cover.instrumentation.callbacks], [PromptFlow][agent_cover.instrumentation.promptflow]:**
    These components do **not** check this context.
* **Reason:** Their execution implies inherent relevance.
    * An **LLM Call** is an expensive I/O operation representing the agent's output/decision.
    * **Framework Callbacks** and **PromptFlow** internals are structurally bound to the framework's lifecycle.
    Therefore, they are tracked unconditionally, regardless of the context state.
"""

import contextvars


class AgentContextManager:
    """Manages the execution context using a thread-safe/async-safe ContextVar.

    This manager acts as a switch. When an agent starts (e.g. `agent.invoke()`),
    the instrumentor calls `set_active(True)`. Only when this switch is True
    does AgentCover record executions.

    This prevents false positives, such as recording an LLM call made during
    test setup as "Agent Coverage".

    Attributes:
        _var: A contextvars.ContextVar that stores the boolean state of the
            agent context (defaults to False).

    Methods:
        set_active(active): Sets the agent context to the specified boolean value.
        reset(token): Resets the agent context to its previous state.
        is_active(): Returns whether the agent context is currently active.
    """

    def __init__(self):
        """Initializes a new AgentContextManager instance."""
        # contextvars.ContextVar to store the agent context state.
        # Defaults to False (not in agent context).
        self._var = contextvars.ContextVar("agent_context", default=False)

    def set_active(self, active: bool) -> contextvars.Token:
        """Sets the agent context to active or inactive.

        Args:
            active: True to activate the agent context, False to deactivate.

        Returns:
            A contextvars.Token that can be used to reset the context to its
            previous state.
        """
        return self._var.set(active)

    def reset(self, token: contextvars.Token):
        """Resets the agent context to its previous state using a token.

        Args:
            token: The token returned by `set_active()` used to restore the
                context.
        """
        self._var.reset(token)

    def is_active(self) -> bool:
        """Checks if the agent context is currently active.

        Returns:
            True if the agent context is active, False otherwise.
        """
        return self._var.get()


# --- Global Instance & Backward Compatibility ---

# Maintains a default singleton instance for backwards compatibility,
# for users who use the library without explicitly using a Manager.
_global_context_manager = AgentContextManager()


def set_agent_context(active: bool) -> contextvars.Token:
    """Sets the global agent context to active or inactive.

    This function is provided for backward compatibility and uses the
    default global context manager instance.

    Args:
        active: True to activate the agent context, False to deactivate.

    Returns:
        A contextvars.Token that can be used to reset the context.
    """
    return _global_context_manager.set_active(active)


def reset_agent_context(token: contextvars.Token):
    """Resets the global agent context to its previous state.

    This function is provided for backward compatibility and uses the
    default global context manager instance.

    Args:
        token: The token returned by `set_agent_context()` to reset the context.
    """
    _global_context_manager.reset(token)


def is_in_agent_context() -> bool:
    """Checks if the global agent context is currently active.

    This function is provided for backward compatibility and uses the
    default global context manager instance.

    Returns:
        True if the agent context is active, False otherwise.
    """
    return _global_context_manager.is_active()


def get_global_context_manager() -> AgentContextManager:
    """Retrieves the global AgentContextManager instance.

    This function is provided for backward compatibility and allows
    accessing the default context manager instance.

    Returns:
        The global AgentContextManager singleton instance.
    """
    return _global_context_manager
