"""# Tool Instrumentation.

This module tracks the definition and execution of Agent Tools.

## 🔗 Architectural Relationships

The `ToolInstrumentor` connects the static definition of tools with their runtime usage.

* **Depends on:** [AgentContextManager][agent_cover.context.AgentContextManager] (Checks if `active==True` before recording executions).
* **Writes to:** [AgentRegistry][agent_cover.registry.AgentRegistry] (Records `executions` using the Canonical ID).
* **Configured by:** [targets.py][agent_cover.instrumentation.tools.targets] (Defines tool base classes like `BaseTool` or `@tool`).

## ⚙️ How it works

It applies a dual-patching strategy:
1.  **Init Patch:** Captures the tool's definition location (File/Line) when instantiated.
2.  **Execution Patch:** Intercepts `_run` / `invoke`. If the [AgentContext][agent_cover.context] is active, it registers a "hit".


## Usage

```python
from agent_cover.instrumentation.tools import instrument_tools

instrument_tools()

```

"""

from .patcher import ToolInstrumentor, instrument_tools

__all__ = ["ToolInstrumentor", "instrument_tools"]
