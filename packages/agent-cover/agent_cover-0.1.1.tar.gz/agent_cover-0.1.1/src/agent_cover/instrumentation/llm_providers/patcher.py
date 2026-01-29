"""Module for instrumenting LLM (Large Language Model) providers.

This module provides the infrastructure to intercept method calls to various
LLM libraries (like OpenAI), extract the generated content, and pass it to
an analysis engine. It uses a patching strategy to wrap target methods
dynamically.
"""

import functools
import importlib
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

from agent_cover.instrumentation.analyzer import OutputAnalyzer
from agent_cover.instrumentation.base import BaseInstrumentor, PatchManager
from agent_cover.instrumentation.definitions import TargetList
from agent_cover.messages import InstrumentationLogger as Log
from agent_cover.registry import AgentRegistry

from .targets import TYPE_CLASS_METHOD, TYPE_FUNCTION, get_provider_targets

logger = logging.getLogger(__name__)


# --- NEW: PAYLOAD EXTRACTOR INTERFACE ---
class PayloadExtractor:
    """Interface for extracting text content from specific LLM result objects.

    If you want to add support for a new LLM provider (e.g., Anthropic, VertexAI),
    you should subclass this and implement the `extract` method.

    Methods:
        extract(result): Should return the plain text string of the LLM's response.
    """

    def extract(self, result: Any) -> Optional[str]:
        """Extracts the text payload from a result object.

        Args:
            result (Any): The return value from the intercepted LLM call (e.g., an OpenAI object).

        Returns:
            Optional[str]: The extracted text string. Returns `None` if the extractor
            cannot handle this specific result object.
        """
        raise NotImplementedError()


class OpenAIExtractor(PayloadExtractor):
    """Extractor implementation for OpenAI-style response objects.

    This class handles standard OpenAI response dictionaries or objects,
    attempting to retrieve content from 'choices', 'messages', or legacy 'text' fields.

    Methods:
        extract(result): Extracts content from OpenAI response structures.
    """

    def extract(self, result: Any) -> Optional[str]:
        """Extracts text from an OpenAI response object.

        Args:
            result (Any): The OpenAI response object (or dict-like object).

        Returns:
            Optional[str]: The content string if found, otherwise None.
        """
        if hasattr(result, "choices") and len(result.choices) > 0:
            choice = result.choices[0]
            message = getattr(choice, "message", None)
            if message:
                return getattr(message, "content", "")
            return getattr(choice, "text", "")
        return None


class StringExtractor(PayloadExtractor):
    """Extractor implementation for simple string results.

    This class handles cases where the LLM function returns a plain string directly.

    Methods:
        extract(result): Returns the result itself if it is a string.
    """

    def extract(self, result: Any) -> Optional[str]:
        """Validates and returns the result if it is a string.

        Args:
            result (Any): The return value to check.

        Returns:
            Optional[str]: The result string if valid, otherwise None.
        """
        return result if isinstance(result, str) else None


# --- DEFAULT DEPENDENCIES ---
def _default_importer(mod_name: str):
    """Default function to import a module by name."""
    return importlib.import_module(mod_name)


def _default_targets_provider() -> TargetList:
    """Default function to retrieve the list of instrumentation targets."""
    return get_provider_targets()


class LLMProviderInstrumentor(BaseInstrumentor):
    """Instrumentor that sits at the edge of the system (External APIs).

    Unlike other instrumentors that track code coverage, this tracks **Data Coverage**.
    It intercepts the raw string response from the LLM to analyze if business logic
    requirements (Decisions) were met.

    Attributes:
        registry (Optional[AgentRegistry]): The registry for agent components.
        analyzer (OutputAnalyzer): The component responsible for analyzing extracted text.
        importer_func (Callable): Function used to import modules dynamically.
        module_iterator (Callable): Function that returns the current mapping of loaded modules.
        targets_provider (Callable): Function that returns a list of targets to instrument.
        extractors (List[PayloadExtractor]): List of strategies used to parse LLM results.
        is_instrumented (bool): Flag indicating if instrumentation has already run.

    Methods:
        instrument(): Performs the actual patching of target methods.
        _resolve_target(mod, obj_name, patch_type): helper to find the specific object/method to patch.
        _create_wrapper(original_func): Creates the closure that wraps the original method.
        _delegate_extraction(result): Iterates through extractors to parse the result.
    """

    def __init__(
        self,
        registry: Optional[AgentRegistry] = None,
        analyzer: Optional[OutputAnalyzer] = None,
        patch_manager: Optional[PatchManager] = None,
        importer_func: Optional[Callable[[str], Any]] = None,
        module_iterator: Optional[Callable[[], Dict[str, Any]]] = None,
        targets_provider: Optional[Callable[[], TargetList]] = None,
        extractors: Optional[List[PayloadExtractor]] = None,
    ):
        """Initializes the LLMProviderInstrumentor.

        Args:
            registry (Optional[AgentRegistry]): The registry instance.
            analyzer (Optional[OutputAnalyzer]): Custom analyzer instance.
            patch_manager (Optional[PatchManager]): The patch manager for safe patching.
            importer_func (Optional[Callable]): Custom import function.
            module_iterator (Optional[Callable]): Custom module iterator provider (for dependency injection).
            targets_provider (Optional[Callable]): Custom provider for patch targets.
            extractors (Optional[List[PayloadExtractor]]): Custom list of payload extractors.
        """
        super().__init__(
            registry=registry,
            patch_manager=patch_manager,
            importer_func=importer_func,
            module_iterator=module_iterator,
        )
        self.analyzer = analyzer or OutputAnalyzer(registry=self.registry)
        self.targets_provider = targets_provider or _default_targets_provider

        self.extractors = extractors or [OpenAIExtractor(), StringExtractor()]

    def instrument(self):
        """Applies patches to the defined LLM provider targets.

        This method iterates through the targets provided by `targets_provider`.
        It loads the necessary modules (using a snapshot to allow for test isolation)
        and wraps the specified methods/functions to enable output analysis.
        """
        if self.is_instrumented:
            return

        raw_targets = self.targets_provider()
        targets = self._normalize_targets(raw_targets)

        # [MODIFICATION] Use module_iterator for test isolation
        modules_snapshot = self.module_iterator()

        for target in targets:
            if not self._should_instrument(target):
                continue

            mod_name = target.module
            obj_name = target.class_name
            patch_type = target.params.get("type")

            try:
                # Import: Check snapshot instead of global sys.modules
                if mod_name not in modules_snapshot:
                    try:
                        self.importer(mod_name)
                        # Refresh snapshot after import
                        modules_snapshot = self.module_iterator()
                    except ModuleNotFoundError:
                        Log.log_skip_missing_module(logger, mod_name)
                        continue

                # Patching logic
                if mod_name in modules_snapshot:
                    mod = modules_snapshot[mod_name]
                    target_obj, method_name = self._resolve_target(
                        mod, obj_name, patch_type
                    )

                    if target_obj is None:
                        Log.log_skip_missing_attr(logger, mod_name, obj_name)
                        continue

                    if target_obj and method_name and hasattr(target_obj, method_name):
                        original_func = getattr(target_obj, method_name)
                        wrapper = self._create_wrapper(original_func)
                        self._safe_patch(target_obj, method_name, wrapper)

            except Exception as e:
                logger.warning(f"Error: {e}", exc_info=True)

        self.is_instrumented = True

    def _resolve_target(
        self, mod: Any, obj_name: str, patch_type: str
    ) -> Tuple[Optional[Any], Optional[str]]:
        """Resolves the module and method names into actual objects.

        Args:
            mod (Any): The module object.
            obj_name (str): The name of the class or function to target.
            patch_type (str): The type of patch (class method or function).

        Returns:
            Tuple[Optional[Any], Optional[str]]: A tuple containing the target object
            (class or module) and the method name to patch.
        """
        target_obj = None
        method_name = None

        if patch_type == TYPE_CLASS_METHOD and "." in obj_name:
            cls_name, m_name = obj_name.split(".")
            if hasattr(mod, cls_name):
                target_obj = getattr(mod, cls_name)
                method_name = m_name
        elif patch_type == TYPE_FUNCTION:
            if hasattr(mod, obj_name):
                target_obj = mod
                method_name = obj_name
            elif "." in obj_name:
                cls_name, m_name = obj_name.split(".")
                if hasattr(mod, cls_name):
                    target_obj = getattr(mod, cls_name)
                    method_name = m_name
        return target_obj, method_name

    def _create_wrapper(self, original_func: Callable) -> Callable:
        """Creates a wrapper function around the original method.

        The wrapper executes the original function, captures the result, attempts to
        extract the payload, and sends it to the analyzer without altering the
        original return value.

        Args:
            original_func (Callable): The original function/method being patched.

        Returns:
            Callable: The wrapped function.
        """

        @functools.wraps(original_func)
        def wrapper(*args, **kwargs):
            result = original_func(*args, **kwargs)
            try:
                payload = self._delegate_extraction(result)
                if payload:
                    self.analyzer.analyze(payload)
            except Exception as e:
                logger.warning(e, exc_info=True)
            return result

        return wrapper

    def _delegate_extraction(self, result: Any) -> Optional[str]:
        """Delegates the result to the registered extractors.

        Args:
            result (Any): The return value from the instrumented function.

        Returns:
            Optional[str]: The extracted text if any extractor succeeds, otherwise None.
        """
        for extractor in self.extractors:
            try:
                val = extractor.extract(result)
                if val:
                    return val
            except Exception as e:
                logger.warning(e, exc_info=True)
                continue
        return None


# --- Backward Compatibility ---
def instrument_llm_providers() -> LLMProviderInstrumentor:
    """Convenience function to instantiate and run the instrumentor.

    Returns:
        LLMProviderInstrumentor: The initialized and executed instrumentor instance.
    """
    instrumentor = LLMProviderInstrumentor()
    instrumentor.instrument()
    return instrumentor
