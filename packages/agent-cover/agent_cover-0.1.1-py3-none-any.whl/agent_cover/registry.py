"""Agent Registry Module.

This module defines the [AgentRegistry][agent_cover.registry.AgentRegistry], which serves as the central
state store (Single Source of Truth) for the entire coverage session.

## 🔗 Architectural Relationships

The Registry acts as the data synchronization bridge between the **Static Analysis** phase and the **Runtime Instrumentation** phase.

1.  **Static Definitions** (What *should* be tested):
    Populated by Scanners like [scan_raw_string_prompts][agent_cover.instrumentation.raw_strings.scanner.scan_raw_string_prompts],
    [scan_pydantic_models][agent_cover.instrumentation.structures.scanner.scan_pydantic_models], and
    [scan_promptflow_definitions][agent_cover.instrumentation.promptflow.scanner.scan_promptflow_definitions].

2.  **Runtime Executions** (What *was* touched):
    Populated by Instrumentors like [ToolInstrumentor][agent_cover.instrumentation.tools.patcher.ToolInstrumentor]
    and [PromptInstrumentor][agent_cover.instrumentation.prompts.patcher.PromptInstrumentor].

3.  **Decision Verification** (Business Logic):
    Populated by the [OutputAnalyzer][agent_cover.instrumentation.analyzer.OutputAnalyzer], which maps
    LLM outputs to [DecisionConfig][agent_cover.config.DecisionConfig] rules.
"""

import hashlib
import logging
from collections import defaultdict
from typing import Any, Callable, Dict, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Central storage mechanism for agent coverage data.

    This singleton-like class holds the state of the coverage session. It uses
    a **Canonical ID** system to link static code definitions (found by parsing files)
    with runtime objects (intercepted during execution).

    Attributes:
        definitions (Dict[str, Dict[str, Any]]): A map of static definitions found
            in the codebase. Keys are canonical IDs (e.g., `src/agent.py:TOOL:search`).
            Values contain metadata like line numbers, previews, and types.
        executions (Set[str]): A set of canonical IDs that were executed during
            the test run. Presence in this set implies "covered".
        decision_hits (Dict[str, Set[str]]): Tracks business logic validation.
            Maps a Decision ID (from config) to a set of observed values found
            in the agent's output.
        content_map (Dict[str, str]): Maps MD5 hashes of content (like prompt templates)
            to their canonical IDs. This handles cases where runtime objects don't
            have file location metadata but have identical content to static files.
        on_hit_callback (Optional[Callable]): A callback function triggered
            whenever a new execution or decision hit is recorded. Used for
            immediate data flushing in multiprocess environments.

    Examples:
        Checking coverage programmatically:
        ```python
        from agent_cover.registry import get_registry

        registry = get_registry()

        # Check if a specific tool was used
        tool_id = "src/tools.py:TOOL:search_google"
        if tool_id in registry.executions:
            print("Tool was used!")

        # Check decision coverage
        hits = registry.decision_hits.get("intent_classification", set())
        print(f"Observed intents: {hits}")
        ```
    """

    def __init__(self) -> None:
        """Initializes a new AgentRegistry instance."""
        self.definitions: Dict[str, Dict[str, Any]] = {}
        self.executions: Set[str] = set()
        self.decision_hits: Dict[str, Set[str]] = defaultdict(set)

        # Maps for ensuring uniqueness of items.
        self.counters: Dict[str, int] = {}
        self.instruction_map: Dict[Tuple, str] = {}
        self.content_map: Dict[str, str] = {}

        self.on_hit_callback: Optional[Callable[[], None]] = None

    def clear(self) -> None:
        """Clears all stored data in the registry.

        This method resets the registry to its initial state, removing all
        definitions, executions, and decision hits. It is essential for
        cleanup and preventing data contamination between test runs or
        instrumentation sessions.
        """
        self.definitions.clear()
        self.executions.clear()
        self.decision_hits.clear()
        self.counters.clear()
        self.instruction_map.clear()
        self.content_map.clear()

    def reset(self) -> None:
        """Resets the registry.

        This method is an alias for the `clear()` method, providing a
        convenient way to reset the registry.
        """
        self.clear()

    def register_content_map(self, content_str: str, known_id: str) -> None:
        """Registers a mapping between the content hash and the canonical ID.

        This method computes the MD5 hash of the given content string and
        associates it with the provided known ID. This allows for
        efficient lookup and ensures uniqueness based on content.

        Args:
            content_str: The string content to hash.
            known_id: The canonical ID to associate with the content hash.
        """
        content_hash = hashlib.md5(content_str.encode("utf-8")).hexdigest()
        self.content_map[content_hash] = known_id

    def get_canonical_id(self, content_str: str, current_id: str) -> str:
        """Retrieves or registers a canonical ID for a given content string.

        This method is essential for mapping runtime objects (which might not have
        filename info) back to statically scanned files based on content hashing.

        Args:
            content_str: The string content (e.g., prompt template text) to hash.
            current_id: The fallback ID to use if this content hasn't been seen before.

        Returns:
            str: The existing canonical ID if the content matches a known definition,
            otherwise returns `current_id` and registers it.
        """
        content_hash = hashlib.md5(content_str.encode("utf-8")).hexdigest()
        if content_hash in self.content_map:
            return self.content_map[content_hash]

        self.content_map[content_hash] = current_id
        return current_id

    def register_definition(
        self, key: str, kind: str, metadata: Dict[str, Any]
    ) -> None:
        """Registers or updates a definition in the registry.

        This method adds a new definition to the registry, associating it
        with a unique key. If the key exists, the definition is updated with
        the new metadata, merging it with existing data.

        Args:
            key: The unique key for the definition.
            kind: The type/kind of the definition (e.g., "PROMPT", "TOOL").
            metadata: A dictionary containing the metadata for the definition.
        """
        new_data = {"type": kind, **metadata}

        if key in self.definitions:
            self.definitions[key].update(new_data)
        else:
            self.definitions[key] = new_data

    def register_execution(self, key: str) -> None:
        """Registers an execution in the registry.

        If the key is new, it adds it to the set of executed items and
        triggers the synchronization callback if configured.

        Args:
            key (str): The unique identifier of the executed component.
        """
        if key not in self.executions:
            self.executions.add(key)

            # Trigger immediate flush/sync if we are in a worker process
            if self.on_hit_callback:
                self.on_hit_callback()

    def register_decision_hit(self, decision_id: str, value: Any) -> None:
        """Registers an observed value for a specific business decision rule.

        Args:
            decision_id (str): The ID of the decision rule from configuration.
            value (Any): The value observed during runtime (will be cast to string).
        """
        val_str = str(value)
        if val_str not in self.decision_hits[decision_id]:
            self.decision_hits[decision_id].add(val_str)

            # Ensure decision hits also trigger synchronization
            if self.on_hit_callback:
                self.on_hit_callback()

    def merge(self, other_data: Dict[str, Any]) -> None:
        """Merges coverage data from an external fragment into the current registry.

        This is used by the CLI aggregator to consolidate results from multiple
        worker processes into a single source of truth.

        Args:
            other_data (Dict[str, Any]): A dictionary containing 'executions',
                'decision_hits', and 'definitions' keys.
        """
        # 1. Merge Executions (Code coverage)
        if "executions" in other_data:
            new_execs = set(other_data["executions"])
            self.executions.update(new_execs)

        # 2. Merge Decision Hits (Business Logic coverage)
        if "decision_hits" in other_data:
            for d_id, hits in other_data["decision_hits"].items():
                self.decision_hits[d_id].update(hits)

        # 3. Merge Definitions (Metadata mapping)
        # Required for the consolidated report to recognize worker-discovered items
        if "definitions" in other_data:
            for key, meta in other_data["definitions"].items():
                if key not in self.definitions:
                    self.definitions[key] = meta

        logger.debug("Successfully merged data fragment into registry.")


# Global instance of the AgentRegistry.
_global_registry = AgentRegistry()


def get_registry() -> AgentRegistry:
    """Retrieves the global AgentRegistry instance.

    This function provides a global access point to the AgentRegistry,
    ensuring a single instance is used throughout the application.

    Returns:
        The global AgentRegistry instance.
    """
    return _global_registry


# Alias for easy access to the global registry instance.
registry = _global_registry
