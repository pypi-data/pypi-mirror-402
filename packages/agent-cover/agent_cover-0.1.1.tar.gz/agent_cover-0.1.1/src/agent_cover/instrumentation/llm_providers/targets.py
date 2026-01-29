"""Definitions of instrumentation targets for LLM providers.

This module contains the configuration and registry of third-party libraries,
modules, and specific methods that the agent coverage tool targets for
instrumentation. It defines constants for patch types and lists the
supported providers with their respective version constraints.
"""

from agent_cover.instrumentation.definitions import TargetList

# --- Constants ---

TYPE_CLASS_METHOD = "class_method"
"""str: Indicates that the target to patch is a method belonging to a class."""

TYPE_FUNCTION = "function"
"""str: Indicates that the target to patch is a standalone function or module-level callable."""


# --- Provider Registry ---

SUPPORTED_PROVIDERS: TargetList = [
    # --- OpenAI v1.x / v2.x (Chat Completions) ---
    {
        "module": "openai.resources.chat.completions.completions",
        "class_name": "Completions.create",
        "params": {"type": TYPE_CLASS_METHOD},
    },
    {
        "module": "openai.resources.chat.completions",
        "class_name": "Completions.create",
        "params": {"type": TYPE_CLASS_METHOD},
        "min_version": "1.0.0",
    },
    # --- OpenAI v1.x / v2.x (Standard Completions) ---
    {
        "module": "openai.resources.completions.completions",
        "class_name": "Completions.create",
        "params": {"type": TYPE_CLASS_METHOD},
    },
    {
        "module": "openai.resources.completions",
        "class_name": "Completions.create",
        "params": {"type": TYPE_CLASS_METHOD},
    },
    # --- OpenAI v0.x (Legacy Module functions) ---
    {
        "module": "openai",
        "class_name": "ChatCompletion.create",
        "params": {"type": TYPE_FUNCTION},
        "max_version": "1.0.0",
    },
    {
        "module": "openai",
        "class_name": "Completion.create",
        "params": {"type": TYPE_FUNCTION},
        "max_version": "1.0.0",
    },
]
"""TargetList: A list of dictionaries defining the instrumentation targets.

Each entry specifies the module to import, the class or function name to target,
the type of patching required (class method vs function), and optional version
constraints (min_version, max_version).
"""


def get_provider_targets() -> TargetList:
    """Retrieves the list of supported provider targets.

    Returns:
        TargetList: A list of dictionaries, where each dictionary represents
        a specific library method to instrument.
    """
    return SUPPORTED_PROVIDERS
