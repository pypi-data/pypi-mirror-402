"""PromptFlow Instrumentation Targets.

This module defines the list of specific modules and functions within the
PromptFlow ecosystem that AgentCover should instrument.

Attributes:
    SUPPORTED_TARGETS (TargetList): A list of dictionaries defining the target
        modules, class/function names, and specific parameters (such as the
        instrumentation type) for interception.
"""

from agent_cover.instrumentation.definitions import TargetList

SUPPORTED_TARGETS: TargetList = [
    # --- Jinja Rendering ---
    {
        "module": "promptflow.tools.common",
        "class_name": "render_jinja_template",
        "params": {"type": "render"},
    },
    {
        "module": "promptflow.core.tools.common",
        "class_name": "render_jinja_template",
        "params": {"type": "render"},
    },
    # --- PromptFlow Tools Decorator ---
    {
        "module": "promptflow.core",
        "class_name": "tool",
        "params": {"type": "decorator"},
    },
    {
        "module": "promptflow.tools.tool",
        "class_name": "tool",
        "params": {"type": "decorator"},
    },
]


def get_promptflow_targets() -> TargetList:
    """Retrieves the list of supported PromptFlow instrumentation targets.

    Returns:
        TargetList: The list of targets defined in SUPPORTED_TARGETS.
    """
    return SUPPORTED_TARGETS
