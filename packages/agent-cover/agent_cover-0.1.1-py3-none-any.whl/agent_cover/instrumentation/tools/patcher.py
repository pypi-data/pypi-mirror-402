"""Module for instrumenting Agent Tools.

This module provides the `ToolInstrumentor` class, which is responsible for
identifying, patching, and registering agent tools (e.g., LangChain tools).
It handles both the static definition registration (location in code) and
dynamic execution tracking.
"""

import functools
import inspect
import logging
import os
from typing import Any, Callable, Dict, Iterator, List, Optional

from agent_cover.instrumentation.base import BaseInstrumentor, PatchManager
from agent_cover.instrumentation.definitions import TargetList
from agent_cover.messages import InstrumentationLogger as Log
from agent_cover.registry import AgentRegistry
from agent_cover.utils import _get_nested_attr, get_definition_location

from .targets import get_tool_targets

logger = logging.getLogger(__name__)


def _default_targets_provider() -> TargetList:
    """Provides the default list of tool targets to instrument.

    Returns:
        TargetList: A list of tuples containing module name,
        class name, and methods to patch.
    """
    return get_tool_targets()


class ToolInstrumentor(BaseInstrumentor):
    """Instrumentor for Tool classes and decorators.

    This class handles the complexity of tracking tools across different frameworks.
    It distinguishes between:
    - **Class-based Tools**: (e.g., LangChain's `BaseTool`) where we patch `_run` and `_arun`.
    - **Decorated Tools**: (e.g., `@tool`) where we wrap the decorated function.

    It ensures that every tool available to the agent is registered as a "coverage target".

    Methods:
        register_existing_tools: Scans the memory for tools that were instantiated *before* instrumentation started.
        instrument: Applies patches to the classes defined in `targets.py`.
    """

    def __init__(
        self,
        registry: Optional[AgentRegistry] = None,
        context_manager=None,
        patch_manager: Optional[PatchManager] = None,
        module_iterator: Optional[Callable[[], Dict[str, Any]]] = None,
        importer_func: Optional[Callable[[str], Any]] = None,
        targets_provider: Optional[Callable[[], TargetList]] = None,
        stack_walker: Optional[Callable[[Any], Iterator[Any]]] = None,
    ):
        """Initializes the ToolInstrumentor.

        Args:
            registry: The agent registry to record data into.
            context_manager: The context manager for tracking execution flow.
            patch_manager: The manager responsible for applying safe patches.
            module_iterator: A callable that returns the current snapshot of sys.modules.
            importer_func: A callable to import modules dynamically.
            targets_provider: A callable returning specific tool classes to target.
            stack_walker: A callable to walk the stack for location resolution.
        """
        super().__init__(
            registry, context_manager, patch_manager, module_iterator, importer_func
        )
        self.targets_provider = targets_provider or _default_targets_provider
        self.stack_walker = stack_walker

    def instrument(self) -> None:
        """Performs the instrumentation process for tools.

        It iterates through the targets, resolves the classes (e.g. `langchain.tools.BaseTool`),
        and applies a wrapper that records execution to the [`AgentRegistry`][agent_cover.registry.AgentRegistry]
        before delegating to the original method.
        """
        if self.is_instrumented:
            return

        raw_targets = self.targets_provider()
        targets = self._normalize_targets(raw_targets)
        modules_snapshot = self.module_iterator()

        for target in targets:
            if not self._should_instrument(target):
                continue

            mod_name = target.module
            cls_name = target.class_name
            methods_to_patch = target.methods

            # Read the "name_attribute" configuration from the params (default: "name")
            name_attr = target.params.get("name_attribute", "name")

            try:
                if mod_name not in modules_snapshot:
                    try:
                        self.importer(mod_name)
                        modules_snapshot = self.module_iterator()
                    except ModuleNotFoundError:
                        Log.log_skip_missing_module(logger, mod_name)
                        continue
                    except Exception as e:
                        logger.warning(e, exc_info=True)
                        continue

                if mod_name in modules_snapshot:
                    mod = modules_snapshot[mod_name]

                    cls = self._resolve_target_class(mod, cls_name)

                    if cls and "_ac_tool_patched" not in cls.__dict__:
                        # Pass the configured attribute to the patch method
                        if isinstance(methods_to_patch, list):
                            self._patch_tool_class(cls, methods_to_patch, name_attr)
                            logger.debug(
                                f"Patched Tool: {cls_name} (name_attr={name_attr})"
                            )

            except Exception as e:
                logger.warning(f"Error patching tool {cls_name}: {e}", exc_info=True)

        self.register_existing_tools()
        self.is_instrumented = True

    def _patch_tool_class(
        self, cls: Any, methods_to_patch: List[str], name_attr: str = "name"
    ) -> None:
        """Patches a specific tool class.

        Wraps the `__init__` method to register the tool definition upon instantiation
        and wraps execution methods to record tool usage.

        Args:
            cls: The class to patch.
            methods_to_patch: A list of method names (e.g., 'invoke', '_run') to patch.
            name_attr: The dot-notation path to the tool name attribute (e.g. 'name' or 'metadata.name').
        """
        # We save the configuration to the class for runtime use (e.g. in _get_safe_tool_id)
        setattr(cls, "_ac_name_attr", name_attr)

        original_init = cls.__init__

        def patched_init(instance, *args, **kwargs):
            original_init(instance, *args, **kwargs)
            try:
                # Use the helper to retrieve the name based on the configuration
                tool_name = _get_nested_attr(instance, name_attr)

                if tool_name:
                    # Passing the injected stack_walker
                    raw_loc = get_definition_location(
                        registry=self.registry, stack_walker=self.stack_walker
                    )
                    file_path = raw_loc.split(":")[0]
                    line_num = 0
                    try:
                        line_num = int(raw_loc.split(":")[1])
                    except Exception as e:
                        logger.warning(e, exc_info=True)

                    canonical_id = f"{file_path}:TOOL:{tool_name}"
                    object.__setattr__(instance, "_ac_tool_id", canonical_id)

                    self.registry.register_definition(
                        key=canonical_id,
                        kind="TOOL",
                        metadata={
                            "class": cls.__name__,
                            "tool_name": tool_name,
                            "preview": f"Tool: {tool_name}",
                            "line_number": line_num,
                        },
                    )
            except Exception as e:
                logger.warning(f"Init patch error: {e}", exc_info=True)

        self._safe_patch(cls, "__init__", patched_init)

        for method_name in methods_to_patch:
            if hasattr(cls, method_name):
                self._apply_execution_patch(cls, method_name)

        cls._ac_tool_patched = True

    def _apply_execution_patch(self, cls: Any, method_name: str) -> None:
        """Applies a wrapper to an execution method (sync or async).

        Args:
            cls: The class containing the method.
            method_name: The name of the method to wrap.
        """
        original_method = getattr(cls, method_name)
        is_async = inspect.iscoroutinefunction(original_method)

        if is_async:

            @functools.wraps(original_method)
            async def wrapper(instance, *args, **kwargs):
                self._record_tool_usage(instance)
                return await original_method(instance, *args, **kwargs)
        else:

            @functools.wraps(original_method)
            def wrapper(instance, *args, **kwargs):
                self._record_tool_usage(instance)
                return original_method(instance, *args, **kwargs)

        self._safe_patch(cls, method_name, wrapper)

    def _record_tool_usage(self, tool_instance: Any) -> None:
        """Records the usage of a tool in the registry if the context is active.

        Args:
            tool_instance: The instance of the tool being used.
        """
        # This prevents false positives when tools are used in isolation (e.g. unit tests).
        if self.context_manager and not self.context_manager.is_active():
            return

        tool_id = self._get_safe_tool_id(tool_instance)
        if tool_id:
            self.registry.register_execution(tool_id)

    def _get_safe_tool_id(self, tool_instance: Any) -> Optional[str]:
        """Retrieves the canonical ID for a tool instance.

        Args:
            tool_instance: The tool instance.

        Returns:
            Optional[str]: The tool ID string, or None if it cannot be determined.
        """
        if hasattr(tool_instance, "_ac_tool_id"):
            return tool_instance._ac_tool_id

        # Retrieves the configuration injected into the class during patching.
        # If it doesn't exist (e.g., uninstrumented tool or existing_tool), fallback to "name".
        name_attr = getattr(tool_instance, "_ac_name_attr", "name")

        tool_name = _get_nested_attr(tool_instance, name_attr)

        if not tool_name:
            return None
        return f"TOOL:{tool_name}"

    def register_existing_tools(self) -> None:
        """Scans currently loaded modules for tools that may have been missed.

        This is useful for tools instantiated before the instrumentor was initialized.
        It scans variables in loaded modules to find objects that look like tools.
        """
        cwd = os.getcwd()
        modules_snapshot = self.module_iterator()

        for mod_name, mod in list(modules_snapshot.items()):
            if not hasattr(mod, "__file__") or not mod.__file__:
                continue
            mod_file = os.path.abspath(mod.__file__)
            if not mod_file.startswith(cwd) or "site-packages" in mod_file:
                continue

            for name, val in list(vars(mod).items()):
                if name.startswith("_"):
                    continue

                # Basic heuristic: must have invoke/_run
                if (
                    hasattr(val, "invoke")
                    or hasattr(val, "_run")
                    or hasattr(val, "call")
                ):
                    try:
                        if hasattr(val, "_ac_tool_id"):
                            continue

                        # Get the path to the name attribute (if the class has been patched, it will have it)
                        name_attr = getattr(val, "_ac_name_attr", "name")
                        tool_name = _get_nested_attr(val, name_attr)

                        if not tool_name:
                            continue

                        canonical_id = f"{mod_file}:TOOL:{tool_name}"

                        try:
                            object.__setattr__(val, "_ac_tool_id", canonical_id)
                        except Exception as e:
                            logger.warning(e, exc_info=True)

                        if canonical_id not in self.registry.definitions:
                            self.registry.register_definition(
                                key=canonical_id,
                                kind="TOOL",
                                metadata={
                                    "class": val.__class__.__name__,
                                    "tool_name": tool_name,
                                    "preview": f"Tool: {tool_name}",
                                    "line_number": 0,
                                },
                            )
                    except Exception as e:
                        logger.warning(e, exc_info=True)


# --- Backward Compatibility ---
def instrument_tools(registry: Optional[AgentRegistry] = None) -> ToolInstrumentor:
    """Helper function for backward compatibility to instrument tools.

    Args:
        registry: The agent registry.

    Returns:
        ToolInstrumentor: The initialized instrumentor instance.
    """
    instrumentor = ToolInstrumentor(registry=registry)
    instrumentor.instrument()
    return instrumentor
