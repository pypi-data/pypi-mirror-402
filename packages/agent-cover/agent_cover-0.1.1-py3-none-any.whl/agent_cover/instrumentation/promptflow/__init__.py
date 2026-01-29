"""# Microsoft PromptFlow Integration.

This module provides specialized support for the PromptFlow ecosystem.

## 🔗 Architectural Relationships

PromptFlow is unique because it defines logic in YAML files (`flow.dag.yaml`) pointing to external assets.
It operates as a **Context-Agnostic** system because the execution of a flow implies an active agent context.

* **Scans:** File System (via [scan_promptflow_definitions][agent_cover.instrumentation.promptflow.scanner.scan_promptflow_definitions]) to find `.jinja2` templates referenced in DAGs.
* **Patches:** [PromptFlow Runtime][agent_cover.instrumentation.promptflow.patcher.PromptFlowInstrumentor] (`render_jinja_template` and `@tool`).
* **Writes to:** [AgentRegistry][agent_cover.registry.AgentRegistry] (Using `FILE:` prefixes for Jinja templates and `TOOL:` for python nodes).
* **Feeds:** [OutputAnalyzer][agent_cover.instrumentation.analyzer.OutputAnalyzer] (Also inspects tool outputs for decision coverage).

## ⚙️ How it works

The instrumentation works in two phases to link static files to runtime execution without explicit context tracking:

1.  **Static Phase**: Parses `flow.dag.yaml`. Finds nodes of type `prompt`. Registers the associated Jinja file content hash as a coverage target.
2.  **Runtime Phase**: Patches the internal `render_jinja_template`. When executed, we hash the template content and match it back to the ID registered in phase 1.


## Usage

```python
from agent_cover.instrumentation.promptflow import (
    scan_promptflow_definitions,
    instrument_promptflow
)

# 1. Register static assets
scan_promptflow_definitions()

# 2. Track execution
instrument_promptflow()

```

"""

from .patcher import PromptFlowInstrumentor, instrument_promptflow
from .scanner import scan_promptflow_definitions

__all__ = [
    "PromptFlowInstrumentor",
    "instrument_promptflow",
    "scan_promptflow_definitions",
]
