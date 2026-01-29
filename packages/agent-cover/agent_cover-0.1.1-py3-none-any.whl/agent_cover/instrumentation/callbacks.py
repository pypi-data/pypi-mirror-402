"""Module for Langchain callback instrumentation.

## Why Callbacks?

While tools and agents are instrumented via **Direct Patching** (wrapping methods),
**Raw Strings** (e.g., `prompt = "You are a bot"`) present a unique challenge:
they are passive data, not active objects.

We cannot patch a string to notify us when it is used. Instead, we use **Callbacks**
as an "Observation Post":

1.  **The Choke Point:** Every request to an LLM in LangChain goes through the Callback Manager.
2.  **Payload Inspection:** We intercept the `on_llm_start` event.
3.  **Pattern Matching:** We scan the incoming prompt text against the regex patterns
    registered for raw strings.

This allows us to verify that a specific global string variable was actually
rendered and sent to the LLM, even though we never "touched" the variable itself.
"""

import re
from typing import Any, Callable, Dict, List, Optional

try:
    from langchain_core.callbacks import BaseCallbackHandler
except ImportError:
    # Fallback if LangChain is not installed
    class BaseCallbackHandler:  # type: ignore[no-redef]
        """Dummy handler for environments without LangChain."""

        pass


from agent_cover.instrumentation.analyzer import (
    OutputAnalyzer,  # Imports the OutputAnalyzer for analyzing agent outputs
)
from agent_cover.instrumentation.base import (
    BaseInstrumentor,  # Imports the base class for instrumentation
    PatchManager,
)
from agent_cover.registry import (  # Imports AgentRegistry and get_registry for managing registered agents
    AgentRegistry,
    get_registry,
)


class CoverageCallbackHandler(BaseCallbackHandler):
    """A custom callback handler that integrates with AgentCover to track and analyze LLM and tool usage.

    This handler acts as a bridge between the LangChain execution lifecycle and the
    [AgentRegistry][agent_cover.registry.AgentRegistry]. It performs two main tasks:

    1.  **Raw String Detection**: During `on_llm_start`, it scans the prompt text to see if it
        matches any raw string patterns registered in the system.
    2.  **Output Analysis**: During `on_llm_end` or `on_chain_end`, it captures the generated
        text and passes it to the [OutputAnalyzer][agent_cover.instrumentation.analyzer.OutputAnalyzer]
        to verify if business decisions/rules are met.

    Attributes:
        registry (AgentRegistry): The registry instance used to track execution coverage.
        analyzer (OutputAnalyzer): The component used to analyze LLM generations against configured decisions.

    Examples:
        Manually using the handler without the global instrumentor:

        ```python
        from langchain_chat.chat_models import ChatOpenAI
        from agent_cover.instrumentation.callbacks import CoverageCallbackHandler

        # Create the handler
        handler = CoverageCallbackHandler()

        # Pass it to a LangChain model
        llm = ChatOpenAI(callbacks=[handler])
        llm.invoke("Hello world")
        ```
    """

    def __init__(
        self,
        registry: Optional[AgentRegistry] = None,
        analyzer: Optional[OutputAnalyzer] = None,
    ):
        """Initializes the CoverageCallbackHandler.

        Args:
            registry: An optional `AgentRegistry` instance. If not provided,
                the global singleton registry is used.
            analyzer: An optional `OutputAnalyzer` instance. If not provided,
                a new instance is created linked to the registry.
        """
        super().__init__()
        self.registry = (
            registry or get_registry()
        )  # Use provided registry or get the default global registry
        self.analyzer = analyzer or OutputAnalyzer(
            registry=self.registry
        )  # Use provided analyzer or create a new one

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Handles the start of an LLM call to detect raw string usage.

        It concatenates all input prompts into a single text block and checks if
        this block matches any regex patterns defined for "Raw String" prompts
        (variables tracked by [scan_raw_string_prompts][agent_cover.instrumentation.raw_strings.scanner.scan_raw_string_prompts]).

        Args:
            serialized: A dictionary containing the serialized LLM call information.
            prompts: A list of string prompts passed to the LLM.
            **kwargs: Additional keyword arguments.
        """
        full_text = " ".join(prompts)  # Concatenate all prompts into a single string
        self._check_raw_strings(full_text)  # Check for raw strings in the combined text

    async def on_llm_start_async(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Asynchronously handles the start of an LLM call.

        Delegates logic to [on_llm_start][agent_cover.instrumentation.callbacks.CoverageCallbackHandler.on_llm_start].
        """
        self.on_llm_start(
            serialized, prompts, **kwargs
        )  # Delegate to the synchronous method

    def on_chat_model_start(
        self, serialized: Dict[str, Any], messages: List[List[Any]], **kwargs: Any
    ) -> None:
        """Handles the start of a chat model call.

        Iterates through the list of message objects (e.g., `HumanMessage`, `SystemMessage`),
        extracts their `content`, and performs raw string detection.

        Args:
            serialized: Metadata about the chat model.
            messages: A list of lists, where each inner list contains LangChain message objects.
            **kwargs: Additional arguments.
        """
        full_text = ""  # Initialize an empty string to store the combined text
        for sublist in messages:  # Iterate through the sublists of messages
            for msg in sublist:  # Iterate through the messages in each sublist
                if hasattr(
                    msg, "content"
                ):  # Check if the message has a content attribute
                    full_text += (
                        str(msg.content) + " "
                    )  # Append the content to the full text
        self._check_raw_strings(full_text)  # Check for raw strings in the combined text

    async def on_chat_model_start_async(
        self, serialized: Dict[str, Any], messages: List[List[Any]], **kwargs: Any
    ) -> None:
        """Asynchronously handles the start of a chat model call.

        Delegates logic to [on_chat_model_start][agent_cover.instrumentation.callbacks.CoverageCallbackHandler.on_chat_model_start].
        """
        self.on_chat_model_start(
            serialized, messages, **kwargs
        )  # Delegate to the synchronous method

    def _check_raw_strings(self, text: str) -> None:
        """Internal helper to match text against registered string constants.

        This method performs a regex search using patterns stored in the registry
        (metadata field `regex_pattern`). If a match is found, the specific string
        constant is marked as executed.

        Args:
            text: The combined prompt text to scan.
        """
        if not text:  # If the text is empty, return
            return
        for (
            key,
            data,
        ) in (
            self.registry.definitions.items()
        ):  # Iterate through the definitions in the registry
            if (
                data.get("class") == "StringConstant"
            ):  # Check if the definition is a string constant
                regex = data.get(
                    "regex_pattern"
                )  # Get the regex pattern for the string constant
                if regex and re.search(
                    regex, text, re.DOTALL | re.IGNORECASE
                ):  # Check if the regex matches the text
                    self.registry.register_execution(
                        key
                    )  # Register the execution of the key

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """Handles the start of a tool call.

        Note:
            Currently, this method is a placeholder. Tool execution tracking is primarily
            handled by the [ToolInstrumentor][agent_cover.instrumentation.tools.patcher.ToolInstrumentor]
            which patches the tool methods directly, rather than relying on callbacks.
        """
        pass  # Placeholder for tool start handling

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """Handles the end of an LLM call to analyze output quality.

        Extracts the generated text from the `response` object and passes it to the
        `analyzer` to check for Decision Coverage (e.g., "Did the agent output 'REFUND'?").

        Args:
            response: The `LLMResult` object from LangChain containing generations.
            **kwargs: Additional arguments.
        """
        if (
            not response or not response.generations
        ):  # Check if the response or generations are empty
            return
        for gen_list in response.generations:  # Iterate through the generation lists
            for gen in gen_list:  # Iterate through the generations
                if gen.text:  # Check if the generation has text
                    self.analyzer.analyze(
                        gen.text
                    )  # Analyze the generated text using the analyzer

    async def on_llm_end_async(self, response: Any, **kwargs: Any) -> None:
        """Asynchronously handles the end of an LLM call.

        Delegates logic to [on_llm_end][agent_cover.instrumentation.callbacks.CoverageCallbackHandler.on_llm_end].
        """
        self.on_llm_end(response, **kwargs)  # Delegate to the synchronous method

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Handles the end of a chain execution.

        Analyzes the final chain outputs. This is useful for agents that return
        structured dictionaries rather than just raw strings.

        Args:
            outputs: The final dictionary returned by the chain.
            **kwargs: Additional keyword arguments.
        """
        self.analyzer.analyze(outputs)  # Analyze the outputs using the analyzer

    async def on_chain_end_async(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Asynchronously handles the end of a chain execution.

        Delegates logic to [on_chain_end][agent_cover.instrumentation.callbacks.CoverageCallbackHandler.on_chain_end].
        """
        self.on_chain_end(outputs, **kwargs)  # Delegate to the synchronous method


class GlobalCallbackInstrumentor(BaseInstrumentor):
    """Instrumentor that globally injects the CoverageCallbackHandler into LangChain.

    This class performs monkey-patching on `langchain_core.callbacks.manager.CallbackManager`
    and `AsyncCallbackManager`. It wraps their `__init__` methods to automatically
    append a [CoverageCallbackHandler][agent_cover.instrumentation.callbacks.CoverageCallbackHandler]
    to every new manager instance.

    Attributes:
        registry (AgentRegistry): The registry instance.
        handler_factory (Callable): A factory function that returns a new handler instance.

    Methods:
        instrument: Applies the instrumentation to Langchain's callback managers.
        _patch_manager_init: Internal method to patch the __init__ of a manager class.
    """

    def __init__(
        self,
        registry: Optional[AgentRegistry] = None,
        patch_manager: Optional[PatchManager] = None,
        handler_factory: Optional[Callable] = None,
    ):
        """Initializes the instrumentor.

        Args:
            registry: The registry instance.
            patch_manager: The patch manager instance to ensure safe patching.
            handler_factory: Optional factory for dependency injection (testing).
                If None, defaults to creating a real `CoverageCallbackHandler`.
        """
        super().__init__(
            registry=registry, patch_manager=patch_manager
        )  # Initialize the base class with the provided or default registry

        # If a handler factory is not provided (e.g., in a test with a mock), use the default factory
        if handler_factory:
            self.handler_factory = handler_factory  # Use the provided handler factory
        else:
            # Default factory: creates a real handler connected to the current registry
            def _default_factory() -> CoverageCallbackHandler:
                """Default factory function to create a CoverageCallbackHandler instance."""
                return CoverageCallbackHandler(registry=self.registry)

            self.handler_factory = _default_factory  # Assign the default factory

    def instrument(self):
        """Applies the patches to LangChain's CallbackManagers.

        If `langchain_core` is not installed, this method returns silently.
        """
        if self.is_instrumented:  # If already instrumented, return
            return

        try:
            # Import CallbackManager and AsyncCallbackManager from langchain_core
            from langchain_core.callbacks.manager import (
                AsyncCallbackManager,
                CallbackManager,
            )
        except ImportError:
            # If the import fails, return (Langchain not installed)
            return

        # Patch the __init__ method of CallbackManager
        self._patch_manager_init(CallbackManager)
        # Patch the __init__ method of AsyncCallbackManager
        self._patch_manager_init(AsyncCallbackManager)

        self.is_instrumented = True  # Set the is_instrumented flag to True

    def _patch_manager_init(self, manager_cls: type) -> None:
        """Internal helper to patch the `__init__` of a specific manager class.

        Args:
            manager_cls: The CallbackManager or AsyncCallbackManager class to patch.
        """
        if hasattr(
            manager_cls, "__init__"
        ):  # Check if the class has an __init__ method
            # Accessing __init__ on a type is considered unsafe by mypy
            original_init = manager_cls.__init__  # type: ignore[misc]

            def patched_init(
                instance,
                handlers: Optional[List[Any]] = None,
                tags: Optional[List[str]] = None,
                inheritable_tags: Optional[List[str]] = None,
                metadata: Optional[Dict[str, Any]] = None,
                **kwargs: Any,
            ) -> None:
                """The patched __init__ method.

                This method is a wrapper around the original __init__ method. It adds the
                CoverageCallbackHandler to the list of handlers before calling the
                original __init__ method.

                Args:
                    instance: The instance of the CallbackManager or AsyncCallbackManager.
                    handlers: An optional list of existing callback handlers.
                    tags: Optional tags for the callback manager.
                    inheritable_tags: Optional inheritable tags for the callback manager.
                    metadata: Optional metadata for the callback manager.
                    **kwargs: Additional keyword arguments.
                """
                if (
                    handlers is None
                ):  # If no handlers are provided, create an empty list
                    handlers = []

                # Use the injected factory (which can return a Mock) to create the handler
                handlers.append(
                    self.handler_factory()
                )  # Append the CoverageCallbackHandler to the list of handlers

                original_init(
                    instance,
                    handlers=handlers,
                    tags=tags,
                    inheritable_tags=inheritable_tags,
                    metadata=metadata,
                    **kwargs,
                )  # Call the original __init__ method

            self._safe_patch(
                manager_cls, "__init__", patched_init
            )  # Apply the patch using _safe_patch
