"""This module defines the targets for instrumentation.

This module contains a list of supported tools and their methods
for instrumentation purposes.  It defines the structure of the
target definitions, including the module, class name, and methods
to be instrumented.
"""

from agent_cover.instrumentation.definitions import TargetList

SUPPORTED_TOOLS: TargetList = [
    # --- LANGCHAIN ---
    {
        "module": "langchain_core.tools",
        "class_name": "BaseTool",
        "methods": ["invoke", "ainvoke", "run", "arun"],
    },
    {
        "module": "langchain.tools",
        "class_name": "BaseTool",
        "methods": ["invoke", "run"],
    },
    {
        "module": "langchain_core.tools",
        "class_name": "StructuredTool",
        "methods": ["_run", "_arun"],
    },
    {
        "module": "langchain.tools",
        "class_name": "StructuredTool",
        "methods": ["_run", "_arun"],
    },
    # --- LLAMA INDEX (Modern v0.10+) ---
    # Path: llama_index.core...
    {
        "module": "llama_index.core.tools",
        "class_name": "BaseTool",
        "methods": ["__call__", "call", "acall"],
    },
    {
        "module": "llama_index.core.tools",
        "class_name": "FunctionTool",
        "methods": ["__call__", "call"],
        "params": {"name_attribute": "metadata.name"},
    },
    {
        "module": "llama_index.core.tools.function_tool",
        "class_name": "FunctionTool",
        "methods": ["__call__", "call"],
        "params": {"name_attribute": "metadata.name"},
    },
    {
        "module": "llama_index.core.tools.types",
        "class_name": "BaseTool",
        "methods": ["__call__", "call", "acall"],
    },
    # --- LLAMA INDEX (Legacy v0.9.x) ---
    # Path: llama_index.tools...
    {
        "module": "llama_index.tools",
        "class_name": "BaseTool",
        "methods": ["__call__", "call", "acall"],
    },
    {
        "module": "llama_index.tools",
        "class_name": "FunctionTool",
        "methods": ["__call__", "call"],
        "params": {"name_attribute": "metadata.name"},
    },
    {
        "module": "llama_index.tools.function_tool",
        "class_name": "FunctionTool",
        "methods": ["__call__", "call"],
        "params": {"name_attribute": "metadata.name"},
    },
    {
        "module": "llama_index.tools.types",
        "class_name": "BaseTool",
        "methods": ["__call__", "call", "acall"],
    },
]


def get_tool_targets() -> TargetList:
    """Returns the list of supported tools.

    Returns:
        TargetList: A list of dictionaries representing the supported tools.
    """
    return SUPPORTED_TOOLS
