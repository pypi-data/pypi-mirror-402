"""# LLM Provider Instrumentation (Data Coverage).

This module intercepts the final calls to External APIs (LLMs) to verify **Decision Coverage**.

## 🔗 Architectural Relationships

Unlike other instrumentors that track *Code Coverage* (was this line run?), this module
feeds the **Verification Layer**.

* **Feeds:** [OutputAnalyzer][agent_cover.instrumentation.analyzer.OutputAnalyzer] (Sends generated text for analysis).
* **Validates against:** [AgentCoverConfig][agent_cover.config.AgentCoverConfig] (Checks if output matches expected `decisions`).
* **Configured by:** [targets.py][agent_cover.instrumentation.llm_providers.targets] (Defines API methods like `openai.create`).

## ⚙️ How it works

It wraps the synchronous and asynchronous API calls to LLM providers. It does not alter the response returned to your application, but "siphons" a copy of the text to the Analyzer.


## Usage

```python
from agent_cover.instrumentation.llm_providers import instrument_llm_providers

instrument_llm_providers()

```

"""

from .patcher import LLMProviderInstrumentor, instrument_llm_providers

__all__ = ["LLMProviderInstrumentor", "instrument_llm_providers"]
