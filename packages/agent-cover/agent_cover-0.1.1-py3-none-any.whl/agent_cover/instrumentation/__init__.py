"""# Instrumentation Core.

This package orchestrates the interception of agent activities. It employs a **Hybrid Instrumentation Strategy** supported by a shared infrastructure layer.

## 🧠 Instrumentation Strategies

AgentCover distinguishes between **Structured Objects** (like Classes/Methods) and **Unstructured Data** (like Strings).

### 1. Direct Patching (Runtime Wrapping)

We wrap defined Python objects to intercept their lifecycle. Crucially, these patched objects interact to establish and respect the **Execution Scope**.

#### A. The Context System (Avoiding False Positives)
Some components (Tools, Prompts) are ambiguous: they can be called by the Agent *or* by your test setup code (e.g., asserting a prompt matches an expected string). To prevent false positives, we distinguish between **Providers** and **Consumers**:

* **Scope Providers:**
  [Agents][agent_cover.instrumentation.agents] wrap the main entry point (e.g., `invoke`). They **activate** the [AgentContextManager][agent_cover.context.AgentContextManager], signaling "Agent Logic is running".

* **Scope Consumers:**
  [Tools][agent_cover.instrumentation.tools] and [Prompts][agent_cover.instrumentation.prompts] wrap execution methods. They **check** the [AgentContextManager][agent_cover.context.AgentContextManager]. If the scope is inactive, they ignore the call.

#### B. Context-Agnostic Inspectors
Certain components inherently belong to the agent's runtime or represent system boundaries. They do **not** check the `AgentContextManager` because their execution implies a relevant event:

* **[LLM Providers][agent_cover.instrumentation.llm_providers]:**
  Wraps API calls (e.g., `openai.create`).
  * **Why Agnostic:** An LLM call is an expensive I/O operation that defines the agent's behavior. Whether it happens inside a framework or in a custom script, it is always a "Decision Point" worth analyzing. It represents the *result* of the agent's thinking, so we capture it unconditionally.

* **[PromptFlow Runtime][agent_cover.instrumentation.promptflow]:**
  Wraps PromptFlow internals (`render_jinja_template`, `@tool`).
  * **Why Agnostic:** PromptFlow is an orchestration framework. If its internal rendering functions are called, the agent execution is essentially active by definition.

* **[Callbacks][agent_cover.instrumentation.callbacks] (detecting [Raw Strings][agent_cover.instrumentation.raw_strings]):**
  Injects listeners into framework event loops (e.g., LangChain).
  * **Why Agnostic:** The Agent's `CallbackManager` is architecturally bound to the agent's lifecycle: it only executes when the agent runs, guaranteeing an implicit valid scope.

**Configuration (targets.py):**
To decouple patching logic from library definitions, each instrumentor relies on a specific `targets.py` registry (e.g., [agents.targets][agent_cover.instrumentation.agents.targets]).

### 2. Callback Injection (Event Listening)
**Used for:** [Raw Strings][agent_cover.instrumentation.raw_strings].

**Why:** You cannot "patch" a python string definition (e.g., `PROMPT = "..."`).
To track if a raw string was used, we must wait until it passes through a choke point. In frameworks like LangChain, the **Callback System** is that choke point.

* We inject a [CoverageCallbackHandler][agent_cover.instrumentation.callbacks.CoverageCallbackHandler] that listens for `on_llm_start`.
* We scan the compiled prompt text sent to the LLM.
* We match this text against the regex patterns discovered by [scan_raw_string_prompts][agent_cover.instrumentation.raw_strings.scanner.scan_raw_string_prompts].

### 3. Static Analysis (Source Scanning)
**Used for:**
[Discovery][agent_cover.discovery],
[Raw Strings Scanner][agent_cover.instrumentation.raw_strings.scanner],
[Structures Scanner][agent_cover.instrumentation.structures.scanner],
[PromptFlow Scanner][agent_cover.instrumentation.promptflow.scanner].

**Why:** Before code runs, we need a "map" of what exists. We scan source files and loaded modules to find:

* **Files & Modules:** The [discovery][agent_cover.discovery] module walks the file system to import user code.
* **Heuristics:** The raw_strings scanner reads source code to find global variables matching specific patterns.
* **Data Structures:** The structures scanner inspects Pydantic models to auto-generate decision rules.
* **Definitions:** The promptflow scanner parses YAML DAGs to identify Jinja templates.

## 🛠️ Core Infrastructure

The strategies above rely on a set of shared components defined in this package:

* **[BaseInstrumentor][agent_cover.instrumentation.base.BaseInstrumentor]** (`base.py`):
    The abstract base class for all instrumentors. It handles the lifecycle of applying/reverting patches (`instrument()`/`uninstrument()`), ensures idempotency (preventing double-patching), and manages [Version Checkers][agent_cover.instrumentation.base.VersionChecker] to skip unsupported library versions.

* **[OutputAnalyzer][agent_cover.instrumentation.analyzer.OutputAnalyzer]** (`analyzer.py`):
    The verification engine. It receives raw text payloads (from LLM providers or callbacks) and performs "Fuzzy Parsing" to check if they satisfy the business rules defined in `agent-cover.yaml`.

* **[PatchManager][agent_cover.instrumentation.base.PatchManager]** (`base.py`):
    A utility that performs the actual `setattr` / `getattr` operations safely, ensuring that original methods can always be restored during cleanup.

* **[WrapperStrategies][agent_cover.instrumentation.strategies]** (`strategies.py`):
    A collection of specialized wrappers (Sync, Async, Generator) that handle the complex logic of maintaining the `ContextVar` state across different execution models.

* **[TargetConfig][agent_cover.instrumentation.definitions.TargetConfig]** (`definitions.py`):
    Data classes used to strictly type the configuration of targets, ensuring validation of module paths and version strings.

## Usage

While mostly used internally by the `pytest` plugin, you can manually trigger instrumentation:

```python
from agent_cover.instrumentation import instrument_all
from agent_cover.registry import get_registry

# 1. Apply patches
instrument_all()

# 2. Run your agent code
my_agent.invoke("Hello world")

# 3. Check registry
reg = get_registry()
print(reg.executions)
```
"""

import logging
import os
from typing import Any, Callable, Dict, Iterator, List, Optional

from agent_cover.config import AgentCoverConfig, get_config
from agent_cover.context import AgentContextManager, get_global_context_manager
from agent_cover.instrumentation.analyzer import OutputAnalyzer
from agent_cover.instrumentation.base import (
    BaseInstrumentor,
    DefaultPatchManager,
    PatchManager,
)
from agent_cover.registry import AgentRegistry, get_registry

from .agents.patcher import AgentInstrumentor
from .callbacks import CoverageCallbackHandler, GlobalCallbackInstrumentor
from .llm_providers.patcher import LLMProviderInstrumentor
from .promptflow.patcher import PromptFlowInstrumentor, instrument_promptflow

# Instrumentation classes imports
from .prompts.patcher import PromptInstrumentor, register_existing_prompts
from .raw_strings.scanner import scan_raw_string_prompts
from .structures.scanner import InspectionProvider, scan_pydantic_models
from .tools.patcher import ToolInstrumentor

__all__ = [
    "instrument_all",
    "scan_static_definitions",
    "AgentInstrumentor",
    "CoverageCallbackHandler",
    "GlobalCallbackInstrumentor",
    "LLMProviderInstrumentor",
    "PromptFlowInstrumentor",
    "instrument_promptflow",
    "PromptInstrumentor",
    "register_existing_prompts",
    "scan_raw_string_prompts",
    "InspectionProvider",
    "scan_pydantic_models",
    "ToolInstrumentor",
]

logger = logging.getLogger(__name__)


def instrument_all(
    registry: Optional[AgentRegistry] = None,
    context_manager: Optional[AgentContextManager] = None,
    patch_manager: Optional[PatchManager] = None,
    analyzer: Optional[OutputAnalyzer] = None,
    config: Optional[AgentCoverConfig] = None,
    # --- DEPENDENCY INJECTION FOR TESTS ---
    importer_func: Optional[Callable[[str], Any]] = None,
    module_iterator: Optional[Callable[[], Dict[str, Any]]] = None,
    inspection_provider: Optional[InspectionProvider] = None,
    targets_provider_map: Optional[Dict[str, Callable]] = None,
    stack_walker: Optional[Callable[[Any], Iterator[Any]]] = None,
) -> List[BaseInstrumentor]:
    """Applies all available instrumentation strategies.

    This function orchestrates the initialization and execution of various
    instrumentors, including raw strings, callbacks, agents, prompts, tools,
    LLM providers, and PromptFlow. It uses dependency injection to allow
    custom implementations for testing purposes.

    Args:
        registry: The agent registry to use. If None, the global registry is used.
        context_manager: The context manager for tracking agent state.
        patch_manager: The manager for applying safe patches.
        analyzer: The analyzer for processing outputs.
        config: The configuration object.
        importer_func: Optional function to import modules (for DI).
        module_iterator: Optional function to iterate over modules (for DI).
        inspection_provider: Optional provider for code inspection (for DI).
        targets_provider_map: Optional map of target providers (for DI).
        stack_walker: Optional function to walk the stack (for DI).

    Returns:
        List[BaseInstrumentor]: A list of successfully initialized and
        active instrumentor instances.
    """
    if registry is None:
        registry = get_registry()
    if context_manager is None:
        context_manager = get_global_context_manager()
    if patch_manager is None:
        patch_manager = DefaultPatchManager()
    if config is None:
        config = get_config()
    if analyzer is None:
        analyzer = OutputAnalyzer(registry=registry, config=config)

    if targets_provider_map is None:
        targets_provider_map = {}

    logger.debug("Initializing instrumentation...")

    active_instrumentors: List[BaseInstrumentor] = []

    # 1. Raw Strings
    try:
        scan_raw_string_prompts(registry=registry, module_iterator=module_iterator)
    except Exception as e:
        logger.warning(f"Failed raw strings scan: {e}", exc_info=True)

    # 2. Callbacks
    try:

        def _handler_factory():
            return CoverageCallbackHandler(registry=registry, analyzer=analyzer)

        cb_inst = GlobalCallbackInstrumentor(
            registry=registry,
            patch_manager=patch_manager,
            handler_factory=_handler_factory,
        )
        cb_inst.instrument()
        active_instrumentors.append(cb_inst)
    except Exception as e:
        logger.warning(f"Failed 2. Callbacks {e}", exc_info=True)

    # 3. Agents
    try:
        agent_inst = AgentInstrumentor(
            registry=registry,
            context_manager=context_manager,
            patch_manager=patch_manager,
            importer_func=importer_func,
            module_iterator=module_iterator,
            targets_provider=targets_provider_map.get("agents"),
        )
        agent_inst.instrument()
        active_instrumentors.append(agent_inst)
    except Exception as e:
        logger.warning(f"Failed 3. Agents {e}", exc_info=True)

    # 4. Prompts
    try:
        p_inst = PromptInstrumentor(
            registry=registry,
            context_manager=context_manager,
            patch_manager=patch_manager,
            importer_func=importer_func,
            module_iterator=module_iterator,
            targets_provider=targets_provider_map.get("prompts"),
            stack_walker=stack_walker,
        )
        p_inst.instrument()
        active_instrumentors.append(p_inst)
    except Exception as e:
        logger.warning(f"Failed 4. Prompts {e}", exc_info=True)

    # 5. Tools
    try:
        t_inst = ToolInstrumentor(
            registry=registry,
            patch_manager=patch_manager,
            importer_func=importer_func,
            module_iterator=module_iterator,
            targets_provider=targets_provider_map.get("tools"),
            stack_walker=stack_walker,
        )
        t_inst.instrument()
        active_instrumentors.append(t_inst)
    except Exception as e:
        logger.warning(f"Failed 5. Tools {e}", exc_info=True)

    # 6. LLM Providers
    try:
        l_inst = LLMProviderInstrumentor(
            registry=registry,
            analyzer=analyzer,
            patch_manager=patch_manager,
            importer_func=importer_func,
            module_iterator=module_iterator,
            targets_provider=targets_provider_map.get("llm"),
        )
        l_inst.instrument()
        active_instrumentors.append(l_inst)
    except Exception as e:
        logger.warning(f"Failed 6. LLM Providers {e}", exc_info=True)

    # 7. PromptFlow
    try:
        pf_inst = PromptFlowInstrumentor(
            registry=registry,
            analyzer=analyzer,
            patch_manager=patch_manager,
            importer_func=importer_func,
            module_iterator=module_iterator,
            targets_provider=targets_provider_map.get("promptflow"),
        )
        pf_inst.instrument()
        active_instrumentors.append(pf_inst)
    except Exception as e:
        logger.warning(
            f"CRITICAL: Failed to initialize PromptFlow instrumentor: {e}",
            exc_info=True,
        )

    # 8. Structures
    try:
        scan_pydantic_models(
            registry=registry,
            config=config,
            module_iterator=module_iterator,
            inspector=inspection_provider,
        )
    except Exception as e:
        logger.warning(f"Failed 8. Structures: {e}", exc_info=True)

    return active_instrumentors


def scan_static_definitions(
    registry: Optional[AgentRegistry] = None,
    config: Optional[AgentCoverConfig] = None,
    root_path: Optional[str] = None,
    module_iterator: Optional[Callable] = None,
    source_reader: Optional[Callable] = None,
    inspector: Optional[InspectionProvider] = None,
):
    """Scans the codebase for static definitions.

    This function triggers static analysis to identify prompts, raw strings,
    and data structures (like Pydantic models) without executing the code.

    Args:
        registry: The agent registry to store findings.
        config: The configuration object.
        root_path: The root directory to scan.
        module_iterator: Optional function to iterate over modules.
        source_reader: Optional function to read source files.
        inspector: Optional provider for code inspection.
    """
    if registry is None:
        registry = get_registry()
    if config is None:
        config = get_config()
    if root_path is None:
        root_path = os.getcwd()

    register_existing_prompts(
        registry=registry, root_path=root_path, module_iterator=module_iterator
    )

    scan_raw_string_prompts(
        registry=registry,
        root_path=root_path,
        module_iterator=module_iterator,
        source_reader=source_reader,
    )

    try:
        scan_pydantic_models(
            registry=registry,
            config=config,
            root_path=root_path,
            module_iterator=module_iterator,
            inspector=inspector,
        )
    except Exception as e:
        logger.warning(f"Struct scan error: {e}", exc_info=True)
