"""AgentCover: Logical coverage metrics for LLM Agents.

This library provides a comprehensive toolkit to measure how well your test
suites exercise an LLM agent's capabilities. Unlike traditional code coverage,
AgentCover focuses on:

1.  **Prompt Coverage**: Ensuring all templates and raw string prompts are used.
2.  **Tool Coverage**: Verifying that the agent effectively invokes its available tools.
3.  **Decision Coverage**: Validating that the LLM's outputs hit all expected
    business logic branches (e.g., specific intents or status codes).

The library utilizes a hybrid instrumentation strategy, combining static
analysis of the codebase with runtime monkey-patching of popular frameworks
like LangChain, LlamaIndex, and PromptFlow.
"""

import logging

logging.getLogger(__name__).addHandler(logging.NullHandler())
