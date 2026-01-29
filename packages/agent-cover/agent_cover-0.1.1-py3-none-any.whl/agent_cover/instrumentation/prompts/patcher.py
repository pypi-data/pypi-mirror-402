"""This module instruments prompt classes to track their execution.

It defines strategies for wrapping the initialization and execution
methods of prompt classes, allowing for the registration of prompt
instances and their executions within the AgentRegistry.
"""

import logging
import os
import sys
from typing import Any, Callable, Dict, Iterator, List, Optional

from agent_cover.context import (
    AgentContextManager,  # Imports the context manager to track the agent's state
)
from agent_cover.instrumentation.base import (  # Base classes for instrumentation
    BaseInstrumentor,
    PatchManager,
)
from agent_cover.instrumentation.definitions import TargetList
from agent_cover.instrumentation.strategies import (
    WrapperStrategy,  # Base class for wrapping methods
)
from agent_cover.messages import InstrumentationLogger as Log
from agent_cover.registry import (  # Imports for the registry to store coverage data
    AgentRegistry,
    get_registry,
)
from agent_cover.utils import (
    _get_nested_attr,  # Helper for robust attribute access
    get_definition_location,  # Utility function to get definition location
)

from .targets import (
    get_prompt_targets,  # Function to get the targets
    # for instrumentation (prompts to patch)
)

logger = logging.getLogger(__name__)


# --- HELPER PER DI ---
def _default_module_iterator() -> Dict[str, Any]:
    """Provides a default iterator for modules.

    Returns:
        A dictionary where keys are module names and values are the module objects.
    """
    return dict(sys.modules)


# --- STRATEGIES SPECIFICHE PER PROMPT ---
class PromptInitStrategy(WrapperStrategy):
    """Strategy for intercepting prompt creation.

    It captures the template content and calculates a unique hash. This allows
    AgentCover to identify the same prompt template even if instantiated in different
    parts of the lifecycle.

    Attributes:
        registry: The AgentRegistry to register the prompt with.
        stack_walker: A callable used to walk the stack and identify the prompt's definition location.

    Methods:
        __init__(registry, stack_walker): Initializes the PromptInitStrategy.
        wrap(original_init, cls_name): Wraps the original __init__ method.
        _register_prompt_instance(instance, cls_name, kwargs): Registers a prompt instance with the AgentRegistry.
    """

    def __init__(
        self, registry: AgentRegistry, stack_walker: Optional[Callable] = None
    ):
        """Initializes the PromptInitStrategy.

        Args:
            registry: The AgentRegistry to register the prompt with.
            stack_walker: A callable used to walk the stack and identify the
                prompt's definition location.
        """
        self.registry = registry
        self.stack_walker = stack_walker

    def wrap(
        self, original_init, cls_name: str, content_attr: Optional[str] = None
    ) -> Callable:
        """Wraps the original __init__ method.

        Args:
            original_init: The original __init__ method of the prompt class.
            cls_name: The name of the class.
            content_attr: The attribute name containing the prompt content (configured in targets).

        Returns:
            A callable that will replace the original __init__ method.
        """

        def patched_init(instance, *args, **kwargs):
            """Patched __init__ method."""
            original_init(instance, *args, **kwargs)
            try:
                self._register_prompt_instance(instance, cls_name, kwargs, content_attr)
            except Exception as e:
                logger.warning(e, exc_info=True)

        return patched_init

    def _register_prompt_instance(self, instance, cls_name, kwargs, content_attr):
        """Registers a prompt instance with the AgentRegistry.

        Args:
            instance: The prompt instance.
            cls_name: The name of the prompt class.
            kwargs: Keyword arguments passed to the __init__ method.
            content_attr: The attribute to check for content.
        """
        raw_id = get_definition_location(
            registry=self.registry, stack_walker=self.stack_walker
        )

        # Uses the configured attribute to find content
        content_str = _get_prompt_content_for_hashing(instance, kwargs, content_attr)
        preview = _get_preview_from_content(content_str)

        canonical_id = self.registry.get_canonical_id(content_str, raw_id)

        self.registry.register_definition(
            key=canonical_id,
            kind="PROMPT",
            metadata={"class": cls_name, "preview": preview},
        )

        # Store the coverage ID on the instance
        object.__setattr__(instance, "_coverage_id", canonical_id)


class PromptExecutionStrategy(WrapperStrategy):
    """Strategy for wrapping prompt execution methods (e.g., generate).

    This strategy registers the execution of a prompt method with the AgentRegistry.

    Methods:
        wrap(original_method, ctx_manager): Wraps the original method.
    """

    def wrap(self, original_method, ctx_manager: AgentContextManager) -> Callable:
        """Wraps the original method.

        Args:
            original_method: The original method of the prompt class.
            ctx_manager: The AgentContextManager to check the agent's context.

        Returns:
            A callable that will replace the original method.
        """

        def wrapper(instance, *args, **kwargs):
            """The patched method.

            This method checks if the agent context is active.
            If it is, it registers the execution with the registry.
            """
            if hasattr(instance, "_coverage_id") and ctx_manager.is_active():
                from agent_cover.registry import (
                    get_registry,  # Import get_registry inside the function
                )

                # Register execution
                get_registry().register_execution(instance._coverage_id)

            return original_method(
                instance, *args, **kwargs
            )  # Call the original method

        return wrapper


# --- HELPER FUNCTIONS ---
def _get_prompt_content_for_hashing(obj, kwargs, attr_name=None):
    """Gets the content of a prompt for hashing.

    It prioritizes the configured 'attr_name' (from targets.py).
    If that fails, it falls back to heuristics.

    Args:
        obj: The prompt object.
        kwargs: Keyword arguments passed to the prompt.
        attr_name: Specific attribute to look for (e.g. 'template' or 'messages').

    Returns:
        The prompt content as a string.
    """
    # 1. Try Configured Attribute
    if attr_name:
        if attr_name in kwargs:
            return str(kwargs[attr_name])
        val = _get_nested_attr(obj, attr_name)
        if val:
            return str(val)

    # 2. Heuristic Fallback (Backward Compatibility)
    if "template" in kwargs:
        return str(kwargs["template"])
    if hasattr(obj, "template"):
        return str(obj.template)

    if "messages" in kwargs:
        return str(kwargs["messages"])
    if hasattr(obj, "messages"):
        return str(obj.messages)

    # LlamaIndex fallback
    if hasattr(obj, "message_templates"):
        return str(obj.message_templates)

    return str(kwargs)


def _get_preview_from_content(content):
    """Gets a preview of the prompt content.

    Args:
        content: The prompt content.

    Returns:
        A preview of the prompt content (first 50 characters).
    """
    clean = content.replace("\n", " ").replace("\r", "")
    return clean[:50]


# --- STATIC SCANNER FUNCTION ---
def register_existing_prompts(
    registry: Optional[AgentRegistry] = None,
    root_path: Optional[str] = None,
    module_iterator: Optional[Callable] = None,
):
    """Registers existing prompts by scanning modules.

    This function scans modules for prompts that are already defined.

    Args:
        registry: The AgentRegistry to register the prompts with.
        root_path: The root path to search for modules.
        module_iterator: A callable to iterate through modules.
    """
    if registry is None:
        registry = get_registry()
    if root_path is None:
        root_path = os.getcwd()
    if module_iterator is None:
        module_iterator = _default_module_iterator

    modules_snapshot = module_iterator()

    for mod_name, mod in modules_snapshot.items():
        if not hasattr(mod, "__file__") or not mod.__file__:
            continue

        try:
            mod_file = os.path.abspath(mod.__file__)

            if not mod_file.startswith(root_path) or "site-packages" in mod_file:
                continue

            for name, val in list(vars(mod).items()):
                if not isinstance(val, type) and (
                    hasattr(val, "template") or hasattr(val, "messages")
                ):
                    content = ""
                    # Note: Static scanning relies on common attribute names as we don't have
                    # the target config here easily without a class lookup map.
                    if hasattr(val, "template") and isinstance(val.template, str):
                        content = val.template
                    elif hasattr(val, "messages"):
                        content = str(val.messages)

                    if content:
                        raw_id = f"{mod_file}:PROMPT:{name}"
                        canonical_id = registry.get_canonical_id(content, raw_id)

                        try:
                            object.__setattr__(val, "_coverage_id", canonical_id)
                        except Exception as e:
                            logger.warning(e, exc_info=True)

                        if canonical_id not in registry.definitions:
                            registry.register_definition(
                                key=canonical_id,
                                kind="PROMPT",
                                metadata={
                                    "class": val.__class__.__name__,
                                    "preview": content[:50].replace("\n", " "),
                                    "file_path": mod_file,
                                    "variable_name": name,
                                },
                            )
                            logger.debug(
                                f"Discovered static prompt: {name} in {mod_name}"
                            )

        except Exception as e:
            logger.warning(f"Error scanning module {mod_name}: {e}", exc_info=True)


# --- INSTRUMENTOR ---


def _default_targets_provider() -> TargetList:
    """Provides the default targets for instrumentation.

    Returns:
        A list of tuples, where each tuple contains the module name, class name, and
        a list of methods to instrument.
    """
    return get_prompt_targets()


class PromptInstrumentor(BaseInstrumentor):
    """Instruments prompt classes to track their definition and runtime usage.

    This instrumentor applies a dual-strategy approach:
    1.  **Init Strategy**: Patches `__init__` to register the prompt instance in the registry immediately upon creation. This establishes the "Total Prompts" count.
    2.  **Execution Strategy**: Patches methods like `format` or `format_messages` to track when a prompt is actually used by the agent.

    Attributes:
        registry (AgentRegistry): The registry to store coverage data.
        init_strategy (PromptInitStrategy): Strategy for wrapping initialization.
        exec_strategy (PromptExecutionStrategy): Strategy for wrapping execution methods.

    Examples:
        How it tracks a LangChain prompt:

        ```python
        # 1. __init__ triggers registration (Definition Coverage)
        prompt = PromptTemplate.from_template("Hello {name}")

        # 2. format() triggers execution (Runtime Coverage)
        prompt.format(name="World")
        ```
    """

    def __init__(
        self,
        registry: Optional[AgentRegistry] = None,
        context_manager: Optional[AgentContextManager] = None,
        patch_manager: Optional[PatchManager] = None,
        module_iterator: Optional[Callable[[], Dict[str, Any]]] = None,
        importer_func: Optional[Callable[[str], Any]] = None,
        targets_provider: Optional[Callable[[], TargetList]] = None,
        # Strategies injection
        init_strategy: Optional[PromptInitStrategy] = None,
        exec_strategy: Optional[PromptExecutionStrategy] = None,
        stack_walker: Optional[Callable[[Any], Iterator[Any]]] = None,
    ):
        """Initializes the PromptInstrumentor.

        Args:
            registry: The AgentRegistry.
            context_manager: The AgentContextManager.
            patch_manager: The PatchManager.
            module_iterator: A callable to iterate through modules.
            importer_func: A function to import modules.
            targets_provider: A callable to provide instrumentation targets.
            init_strategy: The strategy for wrapping the __init__ method.
            exec_strategy: The strategy for wrapping execution methods.
            stack_walker:  A callable used to walk the stack and
            identify the prompt's definition location.
        """
        super().__init__(
            registry, context_manager, patch_manager, module_iterator, importer_func
        )
        self.targets_provider = targets_provider or _default_targets_provider
        self.stack_walker = stack_walker

        # Passiamo lo stack walker alla strategia
        self.init_strategy = init_strategy or PromptInitStrategy(
            self.registry, stack_walker=self.stack_walker
        )
        self.exec_strategy = exec_strategy or PromptExecutionStrategy()

    def instrument(self):
        """Instruments the prompts.

        This method retrieves the targets, iterates through the modules, and applies
        the appropriate strategies to patch the prompt classes.
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

            # Read content attribute from config
            content_attr = target.params.get("content_attribute")

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

                    if cls:
                        # Pass content_attr to the patching method
                        self._patch_prompt_class(cls, methods_to_patch, content_attr)
                        logger.debug(
                            f"Patched Prompt: {cls_name} (content_attr={content_attr})"
                        )

            except Exception as e:
                logger.warning(f"Error patching {cls_name}: {e}", exc_info=True)

        self.is_instrumented = True

    def _patch_prompt_class(
        self, cls, methods_to_patch: List[str], content_attr: Optional[str] = None
    ):
        """Patches a prompt class.

        This method applies the instrumentation strategies to the __init__ and
        specified methods of a prompt class.

        Args:
            cls: The prompt class.
            methods_to_patch: A list of methods to patch.
            content_attr: The attribute to read for content hashing.
        """
        if hasattr(cls, "__init__"):
            original_init = cls.__init__
            # Pass content_attr to the strategy wrapper
            wrapper_init = self.init_strategy.wrap(
                original_init, cls.__name__, content_attr
            )
            self._safe_patch(cls, "__init__", wrapper_init)

        for method_name in methods_to_patch:
            if hasattr(cls, method_name):
                original_method = getattr(cls, method_name)
                wrapper_method = self.exec_strategy.wrap(
                    original_method, self.context_manager
                )
                self._safe_patch(cls, method_name, wrapper_method)


# --- Backward Compatibility ---
def instrument_prompts(registry=None):
    """Backward compatibility function for instrumenting prompts.

    Args:
        registry: The AgentRegistry.

    Returns:
        The PromptInstrumentor instance.
    """
    instrumentor = PromptInstrumentor(registry=registry)
    instrumentor.instrument()
    return instrumentor
