"""Instrumentation module for agent runners.

This module provides the main instrumentor class responsible for applying
wrappers to agent execution methods.

Key Concept: Context Tracking
    This module wraps methods like `AgentExecutor.invoke` to set a "Context Token".
    This allows AgentCover to know when an LLM call is happening *inside* an agent
    versus *outside* (e.g., during test setup), ensuring accurate metrics.
"""

import logging
from typing import Any, Callable, Dict, Optional

from agent_cover.context import AgentContextManager
from agent_cover.instrumentation.base import BaseInstrumentor, PatchManager
from agent_cover.instrumentation.definitions import TargetList
from agent_cover.instrumentation.strategies import (
    AsyncContextWrapper,
    AsyncGenContextWrapper,
    SyncContextWrapper,
    SyncGenContextWrapper,
    WrapperStrategy,
)
from agent_cover.messages import InstrumentationLogger as Log
from agent_cover.registry import AgentRegistry

from .targets import (
    STRATEGY_ASYNC,
    STRATEGY_ASYNC_GEN,
    STRATEGY_SYNC,
    STRATEGY_SYNC_GEN,
    get_agent_targets,
)

DEFAULT_STRATEGIES = {
    STRATEGY_SYNC: SyncContextWrapper(),
    STRATEGY_ASYNC: AsyncContextWrapper(),
    STRATEGY_SYNC_GEN: SyncGenContextWrapper(),
    STRATEGY_ASYNC_GEN: AsyncGenContextWrapper(),
}

logger = logging.getLogger(__name__)


def _default_targets_provider() -> TargetList:
    """Retrieves the default list of agent targets to instrument."""
    return get_agent_targets()


class AgentInstrumentor(BaseInstrumentor):
    """Instruments agent classes with context management strategies.

    This class handles the lifecycle of patching agent runners. It identifies
    target modules, loads them if necessary, resolves the specific classes,
    and wraps execution methods with the appropriate context managers.

    Attributes:
        targets_provider: A callable returning a list of targets to instrument.
        strategies: A dictionary mapping strategy keys to WrapperStrategy instances.
        registry: The agent registry instance.
        context_manager: The context manager for handling agent contexts.
        patch_manager: The manager responsible for applying and reverting patches.
        module_iterator: A callable returning the current snapshot of sys.modules.
        importer_func: A callable used to import modules by name.
        is_instrumented: A boolean indicating if instrumentation has been applied.

    Methods:
        instrument: Performs the instrumentation process on all defined targets.
    """

    def __init__(
        self,
        registry: Optional[AgentRegistry] = None,
        context_manager: Optional[AgentContextManager] = None,
        patch_manager: Optional[PatchManager] = None,
        module_iterator: Optional[Callable[[], Dict[str, Any]]] = None,
        importer_func: Optional[Callable[[str], Any]] = None,
        targets_provider: Optional[Callable[[], TargetList]] = None,
        strategies: Optional[Dict[str, WrapperStrategy]] = None,
    ):
        """Initializes the AgentInstrumentor.

        Args:
            registry: Optional registry for tracking agents.
            context_manager: Optional manager for agent context.
            patch_manager: Optional manager for handling patches.
            module_iterator: Optional callable to get current modules.
            importer_func: Optional callable to import modules.
            targets_provider: Optional callable to provide instrumentation targets.
            strategies: Optional dictionary of instrumentation strategies.
        """
        super().__init__(
            registry, context_manager, patch_manager, module_iterator, importer_func
        )
        self.targets_provider = targets_provider or _default_targets_provider
        self.strategies = strategies or DEFAULT_STRATEGIES

    def instrument(self):
        """Applies instrumentation to all discoverable agent targets.

        This method iterates through the targets provided by the targets_provider.
        It attempts to load the module if it is not present, resolves the target
        class using the base class resolver, and applies the configured wrapper
        strategies to the specified methods.
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
            method_map = target.methods

            try:
                # Attempt lazy import
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

                    # [CHANGE] Use the robust resolver from the base class
                    cls = self._resolve_target_class(mod, cls_name)

                    if cls and "_ac_agent_patched" not in cls.__dict__:
                        self._patch_agent_runner(cls, method_map)
                        cls._ac_agent_patched = True

            except Exception as e:
                logger.warning(e, exc_info=True)

        self.is_instrumented = True

    def _patch_agent_runner(self, cls: Any, method_map: Dict[str, str]):
        """Applies wrappers to the specified methods of an agent class.

        Args:
            cls: The class object to patch.
            method_map: A dictionary mapping method names to strategy keys.
        """
        for method_name, strategy_key in method_map.items():
            if not hasattr(cls, method_name):
                continue

            strategy = self.strategies.get(strategy_key)
            if not strategy:
                continue

            original = getattr(cls, method_name)
            wrapper = strategy.wrap(original, self.context_manager)

            self._safe_patch(cls, method_name, wrapper)


# --- Backward Compatibility ---
def instrument_agents(registry: Optional[AgentRegistry] = None) -> AgentInstrumentor:
    """Helper function to instantiate and run the AgentInstrumentor.

    This function exists primarily for backward compatibility.

    Args:
        registry: An optional AgentRegistry instance.

    Returns:
        The initialized and executed AgentInstrumentor instance.
    """
    instrumentor = AgentInstrumentor(registry=registry)
    instrumentor.instrument()
    return instrumentor
