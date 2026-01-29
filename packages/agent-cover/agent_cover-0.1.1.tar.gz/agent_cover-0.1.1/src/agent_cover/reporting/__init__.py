"""# Report Generation.

This module converts the raw coverage data into human-readable formats.

## 🔗 Architectural Relationships

This is the **Sink** of the data pipeline. It is strictly read-only regarding the registry.

* **Consumes:** [AgentRegistry][agent_cover.registry.AgentRegistry] (Definitions, Executions, Hits).
* **Consumes:** [AgentCoverConfig][agent_cover.config.AgentCoverConfig] (For business logic descriptions).
* **Produces:** HTML Sites and XML Cobertura files.

## ⚙️ How it works

It merges the *Static Definitions* (what exists) with the *Runtime Executions* (what ran) to calculate coverage percentages.


## Usage

```python
from agent_cover.registry import get_registry
from agent_cover.reporting import generate_html_report

reg = get_registry()

generate_html_report(
    definitions=reg.definitions,
    executions=reg.executions,
    output_dir="site/coverage"
)

```

"""

from .html import generate_html_report
from .xml import generate_cobertura_xml

__all__ = ["generate_html_report", "generate_cobertura_xml"]
