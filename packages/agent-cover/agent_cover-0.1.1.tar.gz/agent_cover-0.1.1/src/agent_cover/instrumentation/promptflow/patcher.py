"""Instrumentation module for PromptFlow integration.

This module handles the runtime patching of PromptFlow components to track
executions, render operations, and tool usages within the AgentCover framework.
"""

import functools
import importlib
import inspect
import logging
import os
from typing import Any, Callable, Dict, Optional

from agent_cover.context import get_global_context_manager
from agent_cover.instrumentation.analyzer import OutputAnalyzer
from agent_cover.instrumentation.base import BaseInstrumentor, PatchManager
from agent_cover.instrumentation.definitions import TargetList
from agent_cover.messages import InstrumentationLogger as Log
from agent_cover.registry import AgentRegistry

from .targets import get_promptflow_targets

logger = logging.getLogger(__name__)


# --- DEFAULT DEPENDENCIES ---
def _default_importer(mod_name: str):
    """Imports a module by name."""
    return importlib.import_module(mod_name)


def _default_targets_provider() -> TargetList:
    """Retrieves the default list of PromptFlow targets."""
    return get_promptflow_targets()


class PromptFlowInstrumentor(BaseInstrumentor):
    """Instruments Microsoft PromptFlow components.

    PromptFlow defines flows using a mix of YAML configuration (`flow.dag.yaml`),
    Python tools (`@tool`), and Jinja2 templates. This instrumentor applies patches
    to track:

    1.  **Template Rendering**: Patches internal render functions to track when a Jinja template is used.
    2.  **Tool Execution**: Wraps the `@tool` decorator to track when a node in the flow is executed.

    It works in tandem with [`scan_promptflow_definitions`][agent_cover.instrumentation.promptflow.scanner.scan_promptflow_definitions]
    which statically registers the files found in the DAG.

    Attributes:
        analyzer (OutputAnalyzer): The analyzer used to process execution results.
        targets_provider (Callable): A function that returns a list of targets to instrument.
        registry (AgentRegistry): The registry where execution data is stored.
        patch_manager (PatchManager): Manager for applying and reverting patches.
        module_iterator (Callable): Function to retrieve current sys.modules.
        importer_func (Callable): Function to import modules dynamically.
        is_instrumented (bool): Flag indicating if instrumentation has already run.

    Methods:
        instrument(): Applies patches to the target PromptFlow modules.
    """

    def __init__(
        self,
        registry: Optional[AgentRegistry] = None,
        analyzer: Optional[OutputAnalyzer] = None,
        patch_manager: Optional[PatchManager] = None,
        module_iterator: Optional[Callable[[], Dict[str, Any]]] = None,
        importer_func: Optional[Callable[[str], Any]] = None,
        targets_provider: Optional[Callable[[], TargetList]] = None,
    ):
        """Initializes the PromptFlowInstrumentor.

        Args:
            registry: The agent registry instance.
            analyzer: Optional output analyzer instance.
            patch_manager: Optional patch manager instance.
            module_iterator: Optional callable to get current modules.
            importer_func: Optional callable to import modules.
            targets_provider: Optional callable to provide instrumentation targets.
        """
        super().__init__(
            registry=registry,
            patch_manager=patch_manager,
            module_iterator=module_iterator,
            importer_func=importer_func,
        )
        self.analyzer = analyzer or OutputAnalyzer(registry=self.registry)
        self.targets_provider = targets_provider or _default_targets_provider

    def instrument(self):
        """Applies runtime patches to PromptFlow's core modules.

        It targets:
        - `promptflow.tools.common.render_jinja_template`: To catch prompt usage.
        - `promptflow.core.tool`: To catch python tool usage.

        Note:
            This method is fault-tolerant; if PromptFlow is not installed, it simply
            skips instrumentation without raising errors.
        """
        if self.is_instrumented:
            return

        raw_targets = self.targets_provider()
        targets = self._normalize_targets(raw_targets)

        patched_count = 0

        # [MODIFICATION] Use module_iterator
        modules_snapshot = self.module_iterator()

        for target in targets:
            if not self._should_instrument(target):
                continue

            mod_name = target.module
            obj_name = target.class_name
            target_type = target.params.get("type")

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

                    if hasattr(mod, obj_name):
                        if target_type == "render":
                            self._patch_render_function(mod, obj_name)
                            patched_count += 1
                        elif target_type == "decorator":
                            self._patch_tool_decorator(mod, obj_name)
                            patched_count += 1

            except Exception as e:
                logger.warning(
                    f"PromptFlow Patch Error ({mod_name}): {e}", exc_info=True
                )

        if patched_count > 0:
            logger.debug(f"Instrumented {patched_count} PromptFlow internals.")

        self.is_instrumented = True

    # --- RENDER PATCHER ---
    def _patch_render_function(self, module: Any, func_name: str):
        """Patches the PromptFlow render function to track Jinja2 template usage.

        This method wraps the internal rendering logic to:
        1. Calculate content hashes and link them to static file definitions.
        2. Analyze the rendered prompt text for decision/business logic coverage.

        Args:
            module (Any): The module containing the render function.
            func_name (str): The name of the rendering function (e.g., 'render_jinja_template').
        """
        original_func = getattr(module, func_name)

        if getattr(original_func, "_ac_patched", False):
            return

        @functools.wraps(original_func)
        def wrapper(template, **kwargs):
            # Execute original rendering to get the final string sent to the LLM
            rendered_prompt = original_func(template, **kwargs)

            try:
                if isinstance(template, str):
                    # 1. Track Prompt Coverage (Jinja)
                    # We use a runtime hash to match this specific template version
                    # back to the statically scanned file IDs.
                    content_hash = f"RUNTIME:PF:{hash(template)}"
                    canonical_id = self.registry.get_canonical_id(
                        template, content_hash
                    )

                    if canonical_id.startswith("FILE:"):
                        self.registry.register_execution(canonical_id)
                        logger.debug(f"PromptFlow template hit: {canonical_id}")

                # 2. Track Decision Coverage (Business Logic)
                # We pass the fully rendered text to the analyzer to check for
                # expected values.
                if rendered_prompt:
                    self.analyzer.analyze(rendered_prompt)

            except Exception as e:
                logger.error(f"Error in PromptFlow render patch: {e}", exc_info=True)

            return rendered_prompt

        self._safe_patch(module, func_name, wrapper)

    # --- TOOL DECORATOR PATCHER ---
    def _patch_tool_decorator(self, module: Any, func_name: str):
        """Patches the @tool decorator to instrument user functions.

        Args:
            module: The module containing the decorator.
            func_name: The name of the decorator function.
        """
        original_tool = getattr(module, func_name)
        if getattr(original_tool, "_ac_patched", False):
            return

        @functools.wraps(original_tool)
        def tool_wrapper(func_or_none=None, **kwargs):
            if func_or_none is not None and callable(func_or_none):
                instrumented_func = self._instrument_user_function(func_or_none)
                return original_tool(instrumented_func)

            def partial_wrapper(user_func):
                instrumented_func = self._instrument_user_function(user_func)
                return original_tool(**kwargs)(instrumented_func)

            return partial_wrapper

        self._safe_patch(module, func_name, tool_wrapper)

    def _instrument_user_function(self, user_func: Callable) -> Callable:
        """Wraps a user-defined tool function to manage context and track execution.

        This wrapper is critical for PromptFlow as it manually activates the
        AgentContextManager. Since PromptFlow doesn't use standard AgentExecutors,
        this ensures that subsequent tool/prompt calls are recorded.

        Args:
            user_func (Callable): The actual tool function decorated by @tool.

        Returns:
            Callable: The instrumented function with context management and tracking.
        """
        try:
            # Resolve tool identification metadata
            source_file = inspect.getsourcefile(user_func)
            source_file = os.path.abspath(source_file) if source_file else "unknown"
            func_name = user_func.__name__
            canonical_id = f"{source_file}:TOOL:{func_name}"

            # Register the tool definition if not already present
            if canonical_id not in self.registry.definitions:
                self.registry.register_definition(
                    key=canonical_id,
                    kind="TOOL",
                    metadata={
                        "class": "PromptFlow::Python",
                        "tool_name": func_name,
                        "preview": f"@tool def {func_name}(...)",
                        "file_path": source_file,
                        "line_number": 0,
                    },
                )
        except Exception as e:
            logger.warning(f"Failed to register PromptFlow tool definition: {e}")

        @functools.wraps(user_func)
        def execution_wrapper(*args, **kwargs):
            # FORCED CONTEXT ACTIVATION
            # We manually set the agent context to active so that the instrumentation
            # core knows we are inside a valid agent logic flow.

            ctx = get_global_context_manager()
            token = ctx.set_active(True)

            logger.debug(
                f"Executing PromptFlow node: {user_func.__name__} (PID: {os.getpid()})"
            )

            try:
                result = user_func(*args, **kwargs)

                # Register execution of the node itself
                try:
                    # Re-calculate ID for recording the execution hit
                    s_file = inspect.getsourcefile(user_func)
                    if s_file:
                        c_id = f"{os.path.abspath(s_file)}:TOOL:{user_func.__name__}"
                        self.registry.register_execution(c_id)
                except Exception as e:
                    logger.warning(e)

                # Pass the tool result to the analyzer for data coverage
                try:
                    self.analyzer.analyze(result)
                except Exception as e:
                    logger.warning(e)

                return result
            finally:
                # Always restore the previous context state
                ctx.reset(token)

        return execution_wrapper


# --- Legacy ---
def instrument_promptflow(registry: Optional[AgentRegistry] = None):
    """Legacy helper function to instantiate and run the instrumentor.

    Args:
        registry: Optional AgentRegistry instance.

    Returns:
        PromptFlowInstrumentor: The instrumentor instance.
    """
    inst = PromptFlowInstrumentor(registry=registry)
    inst.instrument()
    return inst
