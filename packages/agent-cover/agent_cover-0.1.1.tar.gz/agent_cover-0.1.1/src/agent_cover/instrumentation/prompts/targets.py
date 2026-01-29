"""This module defines the targets for instrumenting prompt classes.

It specifies the modules, classes, and methods that AgentCover should
instrument to track prompt usage.
"""

from agent_cover.instrumentation.definitions import TargetList

SUPPORTED_FRAMEWORKS: TargetList = [
    # --- LANGCHAIN ---
    {
        "module": "langchain.prompts",
        "class_name": "PromptTemplate",
        "methods": ["format"],
        "params": {"content_attribute": "template"},
    },
    {
        "module": "langchain.prompts",
        "class_name": "ChatPromptTemplate",
        "methods": ["format_messages", "format"],
        "params": {"content_attribute": "messages"},
    },
    {
        "module": "langchain_core.prompts",
        "class_name": "PromptTemplate",
        "methods": ["format"],
        "params": {"content_attribute": "template"},
    },
    {
        "module": "langchain_core.prompts",
        "class_name": "ChatPromptTemplate",
        "methods": ["format_messages", "format"],
        "params": {"content_attribute": "messages"},
    },
    # --- LLAMA INDEX (Modern v0.10+) ---
    {
        "module": "llama_index.core.prompts",
        "class_name": "PromptTemplate",
        "methods": ["format"],
        "params": {"content_attribute": "template"},
    },
    {
        "module": "llama_index.core.prompts",
        "class_name": "SelectorPromptTemplate",
        "methods": ["format"],
        # Selector often wraps others, but typically has a template structure
        "params": {"content_attribute": "template"},
    },
    {
        "module": "llama_index.core.prompts",
        "class_name": "ChatPromptTemplate",
        "methods": ["format"],
        "params": {"content_attribute": "message_templates"},
    },
    # --- LLAMA INDEX (Legacy v0.9.x) ---
    {
        "module": "llama_index.prompts",
        "class_name": "PromptTemplate",
        "methods": ["format"],
        "params": {"content_attribute": "template"},
    },
    {
        "module": "llama_index.prompts",
        "class_name": "SelectorPromptTemplate",
        "methods": ["format"],
        "params": {"content_attribute": "template"},
    },
    {
        "module": "llama_index.prompts",
        "class_name": "ChatPromptTemplate",
        "methods": ["format"],
        "params": {"content_attribute": "message_templates"},
    },
]


def get_prompt_targets() -> TargetList:
    """Returns the list of supported prompt targets.

    This function provides access to the list of prompt targets that
    AgentCover will instrument.

    Returns:
        A list of dictionaries, where each dictionary represents a
        prompt target.
    """
    return SUPPORTED_FRAMEWORKS
