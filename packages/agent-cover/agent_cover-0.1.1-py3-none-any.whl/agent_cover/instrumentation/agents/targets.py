"""This module defines the targets for instrumenting agent classes.

It specifies the modules, classes, and methods that AgentCover should
instrument to track agent execution.
"""

from agent_cover.instrumentation.definitions import TargetList

STRATEGY_SYNC = "sync"
"""Constant for synchronous execution strategy."""
STRATEGY_ASYNC = "async"
"""Constant for asynchronous execution strategy."""
STRATEGY_SYNC_GEN = "sync_gen"
"""Constant for synchronous generator execution strategy."""
STRATEGY_ASYNC_GEN = "async_gen"
"""Constant for asynchronous generator execution strategy."""

SUPPORTED_AGENTS: TargetList = [
    # --- LANGCHAIN ---
    {
        "module": "langchain.agents",
        "class_name": "AgentExecutor",
        "methods": {
            "invoke": STRATEGY_SYNC,
            "stream": STRATEGY_SYNC_GEN,
            "astream": STRATEGY_ASYNC_GEN,
        },
        "min_version": "0.1.0",
    },
    {
        "module": "langchain.chains",
        "class_name": "LLMChain",
        "methods": {
            "invoke": STRATEGY_SYNC,
        },
    },
    # --- LLAMA INDEX (Modern v0.10+) ---
    {
        "module": "llama_index.core.agent",
        "class_name": "AgentRunner",
        "methods": {
            "chat": STRATEGY_SYNC,
            "achat": STRATEGY_ASYNC,
        },
    },
    # --- LLAMA INDEX (Legacy v0.9.x) ---
    {
        "module": "llama_index.agent",
        "class_name": "AgentRunner",
        "methods": {
            "chat": STRATEGY_SYNC,
            "achat": STRATEGY_ASYNC,
        },
    },
    {
        "module": "llama_index.agent.runner.base",
        "class_name": "AgentRunner",
        "methods": {
            "chat": STRATEGY_SYNC,
            "achat": STRATEGY_ASYNC,
        },
    },
]


def get_agent_targets() -> TargetList:
    """Returns the list of supported agent targets.

    This function provides access to the list of agent targets that
    AgentCover will instrument.

    Returns:
        A list of dictionaries, where each dictionary represents an
        agent target.
    """
    return SUPPORTED_AGENTS
