"""# Agent Instrumentation (Scope Management).

This module hooks into high-level Agent orchestrators (like LangChain's `AgentExecutor`).

## 🔗 Architectural Relationships

The `AgentInstrumentor` acts as the **Scope Manager** for the entire library.
It does not directly measure coverage; instead, it signals *when* an agent is running.

* **Controls:** [AgentContextManager][agent_cover.context.AgentContextManager] (Sets `active=True`).
* **Influences:** [ToolInstrumentor][agent_cover.instrumentation.tools] and [PromptInstrumentor][agent_cover.instrumentation.prompts] (They only record data when this module sets the context to active).
* **Configured by:** [targets.py][agent_cover.instrumentation.agents.targets] (Defines which classes trigger the scope).

## ⚙️ How it works

When you run `agent.invoke(...)`, this instrumentor wraps the call to ensure that any
subsequent tool usage or prompt formatting is correctly attributed to the agent run,
ignoring calls made during test setup.


## Usage

```python
from agent_cover.instrumentation.agents import instrument_agents

# Patches classes defined in targets.py
instrument_agents()

```

"""

from .patcher import AgentInstrumentor, instrument_agents

__all__ = ["AgentInstrumentor", "instrument_agents"]
