"""# Data Structure Analysis (Decision Generator).

This module is the backbone of automated "Decision Coverage".

## 🔗 Architectural Relationships

This module bridges the gap between **Type Definitions** and **Test Assertions**.

* **Inspects:** [Pydantic Models][agent_cover.instrumentation.structures.adapters.PydanticAdapter] and Dataclasses.
* **Populates:** [AgentCoverConfig][agent_cover.config.AgentCoverConfig] (Automatically appends new `DecisionConfig` rules).
* **Influences:** [OutputAnalyzer][agent_cover.instrumentation.analyzer.OutputAnalyzer] (The analyzer uses the rules generated here to validate output).

## ⚙️ How it works

It scans imported modules for classes. If it finds a Pydantic model with finite fields (Enum, Literal, Bool), it converts them into coverage requirements.


## Usage

```python
from agent_cover.instrumentation.structures import scan_pydantic_models

# Scans loaded modules and populates the global config
scan_pydantic_models()

```

"""

from .scanner import InspectionProvider, scan_pydantic_models

__all__ = ["scan_pydantic_models", "InspectionProvider"]
