"""# Prompt Instrumentation.

This module intercepts the initialization and formatting of Prompt Templates.

## 🔗 Architectural Relationships

Prompts are unique because they are often defined globally but used locally.
This module links these two states.

* **Populates:** [AgentRegistry][agent_cover.registry.AgentRegistry] (Both `definitions` and `executions`).
* **Depends on:** [AgentContextManager][agent_cover.context.AgentContextManager] (Only tracks formatting if inside an agent loop).
* **Complementary to:** [Raw Strings Scanner][agent_cover.instrumentation.raw_strings] (This module handles Objects; the scanner handles Strings).

## ⚙️ How it works

1.  **Init Strategy**: Patches `__init__`. Calculates a hash of the template text to create a stable ID, linking runtime objects to static files.
2.  **Execution Strategy**: Patches `format`. Registers usage when the prompt is filled with variables.


## Usage

```python
from agent_cover.instrumentation.prompts import instrument_prompts

instrument_prompts()

```

"""

from .patcher import (
    PromptInstrumentor,
    instrument_prompts,
    register_existing_prompts,
)

__all__ = ["PromptInstrumentor", "instrument_prompts", "register_existing_prompts"]
