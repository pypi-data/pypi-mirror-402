"""Main entry point for managing agent coverage instrumentation.

This module acts as the **Controller** of the library. It orchestrates the
lifecycle of the coverage process, ensuring that all components (Registry,
Config, Context, Instrumentors) are initialized in the correct order and
wired together via Dependency Injection.
"""

import logging
from typing import Any, Callable, Dict, Iterator, List, Optional

from agent_cover.config import AgentCoverConfig
from agent_cover.context import AgentContextManager
from agent_cover.instrumentation import instrument_all
from agent_cover.instrumentation.analyzer import OutputAnalyzer
from agent_cover.instrumentation.base import (
    BaseInstrumentor,
    DefaultPatchManager,
    PatchManager,
    VersionChecker,
)
from agent_cover.instrumentation.structures.scanner import InspectionProvider
from agent_cover.registry import AgentRegistry


class AgentCoverage:
    """Lifecycle manager for the AgentCover system.

    This class corresponds to a single test session. It orchestrates initialization,
    instrumentation, and cleanup.

    Attributes:
        registry (AgentRegistry): The storage for coverage data.
        config (AgentCoverConfig): The loaded configuration.
        instrumentors (List[BaseInstrumentor]): List of active instrumentors.

    Examples:
        **Using the Context Manager (Recommended):**

        This ensures that patches are applied at the start and safely removed at the end.

        ```python
        from agent_cover.manager import AgentCoverage

        def main():
            # Initialize coverage
            with AgentCoverage() as coverage:
                # ... Run your agent logic here ...
                my_agent.invoke("Hello world")

                # Access coverage data programmatically
                print(f"Executions: {len(coverage.registry.executions)}")
            # Patches are removed automatically here
        ```
    """

    def __init__(
        self,
        registry: Optional[AgentRegistry] = None,
        config: Optional[AgentCoverConfig] = None,
        context_manager: Optional[AgentContextManager] = None,
        analyzer: Optional[OutputAnalyzer] = None,
        patch_manager: Optional[PatchManager] = None,
    ):
        """Initializes the AgentCoverage manager.

        Args:
            registry: Optional custom registry. Defaults to a new AgentRegistry.
            config: Optional custom config. Defaults to a new AgentCoverConfig.
            context_manager: Optional custom context manager. Defaults to a new AgentContextManager.
            analyzer: Optional custom output analyzer. Defaults to a new OutputAnalyzer.
            patch_manager: Optional custom patch manager. Defaults to DefaultPatchManager.
        """
        self.registry = registry or AgentRegistry()
        self.config = config or AgentCoverConfig()
        self.context_manager = context_manager or AgentContextManager()
        self.logger = logging.getLogger(__name__)  # Standard logging
        self.analyzer = analyzer or OutputAnalyzer(
            registry=self.registry, config=self.config
        )
        self.patch_manager = patch_manager or DefaultPatchManager()

        self.instrumentors: List[BaseInstrumentor] = []
        self._is_active = False

    def start(
        self,
        # --- TEST HOOKS & DI ---
        importer_func: Optional[Callable[[str], Any]] = None,
        module_iterator: Optional[Callable[[], Dict[str, Any]]] = None,
        inspection_provider: Optional[InspectionProvider] = None,
        targets_provider_map: Optional[Dict[str, Callable]] = None,
        version_checker: Optional[VersionChecker] = None,
        stack_walker: Optional[Callable[[Any], Iterator[Any]]] = None,
    ):
        """Starts the instrumentation process.

        This method initializes all necessary instrumentors. It supports dependency
        injection for various internal components to facilitate testing.

        Args:
            importer_func: Optional function to import modules (for DI/testing).
            module_iterator: Optional function to iterate over modules (for DI/testing).
            inspection_provider: Optional provider for code inspection (for DI/testing).
            targets_provider_map: Optional map for target providers (for DI/testing).
            version_checker: Optional version checker instance (for DI/testing).
            stack_walker: Optional callable for walking the stack (for DI/testing).
        """
        if self._is_active:
            self.logger.warning("AgentCoverage is already active.")
            return

        # In instrument_all, each instrumentor will create its own logger
        # based on its module name.
        self.instrumentors = instrument_all(
            registry=self.registry,
            context_manager=self.context_manager,
            patch_manager=self.patch_manager,
            analyzer=self.analyzer,
            config=self.config,
            # DI
            importer_func=importer_func,
            module_iterator=module_iterator,
            inspection_provider=inspection_provider,
            targets_provider_map=targets_provider_map,
            stack_walker=stack_walker,
        )

        # Apply the version checker if provided (e.g., Mock for tests).
        if version_checker:
            for inst in self.instrumentors:
                if hasattr(inst, "version_checker"):
                    inst.version_checker = version_checker

        self._is_active = True
        self.logger.info("Instrumentation started.")

    def stop(self):
        """Stops the instrumentation in an idempotent and safe manner.

        This method reverts all applied patches by uninstrumenting the
        components in reverse order of their initialization.
        """
        if not self._is_active:
            return

        self.logger.info("Stopping instrumentation...")

        for inst in reversed(list(self.instrumentors)):
            try:
                inst.uninstrument()
            except Exception as e:
                self.logger.error(
                    f"Error uninstrumenting {inst.__class__.__name__}: {e}"
                )

        self.instrumentors.clear()
        self._is_active = False

    def __enter__(self):
        """Context manager entry point. Calls start()."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point. Calls stop()."""
        self.stop()
