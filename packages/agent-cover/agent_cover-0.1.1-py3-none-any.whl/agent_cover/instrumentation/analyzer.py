"""Module for analyzing agent outputs against configured decisions.

This module implements the **Verification Layer** of AgentCover. While other
modules track *if* code ran, this module tracks *what* the code produced.

Flow:
    1. **Interception**: Instrumentors capture generated text.
    2. **Normalization**: `OutputAnalyzer` converts inputs (Strings, Pydantic, Dicts) to a standard dict.
    3. **Evaluation**: Compares data against [`DecisionConfig`][agent_cover.config.DecisionConfig].
"""

import json
import logging
import re
from typing import Any, Optional

# Imports for configuration management
from agent_cover.config import AgentCoverConfig, get_config

# Imports for data adapters and structures
from agent_cover.instrumentation.structures.adapters import (
    AdapterRegistry,
    get_default_adapter_registry,
)

# Imports for the registry system
from agent_cover.registry import AgentRegistry, get_registry

logger = logging.getLogger(__name__)


class OutputAnalyzer:
    """Analyzes agent outputs to verify business logic coverage.

    This class decouples data extraction from validation. It is robust to
    different data formats, capable of parsing JSON strings embedded in Markdown
    or handling raw Pydantic models.

    Key Features:
        - **Adapter System**: Automatically handles Pydantic V1/V2 and Dataclasses.
        - **Fuzzy JSON Parsing**: Can extract JSON from messy LLM outputs (e.g., wrapped in markdown code blocks).
        - **Decision Matching**: Registers hits in the registry when output fields match expected values.

    Attributes:
        registry (AgentRegistry): Where decision hits are recorded.
        config (AgentCoverConfig): Source of the decision rules.
        adapter_registry (AdapterRegistry): Registry for converting objects to dicts.
    """

    def __init__(
        self,
        registry: Optional[AgentRegistry] = None,
        config: Optional[AgentCoverConfig] = None,
        adapter_registry: Optional[AdapterRegistry] = None,
    ):
        """Initializes the OutputAnalyzer.

        Args:
            registry: The AgentRegistry instance.
            config: The AgentCoverConfig instance.
            adapter_registry: The adapter registry to use for data conversion.
        """
        # Use provided registry or get the default global registry
        self.registry = registry or get_registry()
        # Use provided config or get the default global config
        self.config = config or get_config()
        # Use the injected adapter registry or the default global adapter registry
        self.adapter_registry = adapter_registry or get_default_adapter_registry()

    def analyze(self, payload: Any) -> None:
        r"""Analyzes the given payload to detect matches against configured decisions.

        The method handles three types of payloads:
        1. **Objects**: Uses adapters to convert Pydantic/Dataclasses to dicts.
        2. **Dictionaries**: Analyzes fields directly.
        3. **Strings**: Attempts to parse JSON. If parsing fails, performs substring matching.

        Args:
            payload (Any): The output to analyze. Can be a Dict, str, Pydantic Model, etc.

        Examples:
            >>> analyzer.analyze({"intent": "REFUND", "confidence": 0.9})
            # Registers a hit for decision with target_field="intent" and expected_values=["REFUND"]

            >>> analyzer.analyze("The user wants to buy something.")
            # Registers a hit if a decision expects "buy" in the raw text.

            >>> analyzer.analyze("```json\n{'status': 'DONE'}\n```")
            # fuzzy parses JSON and matches status=DONE.
        """
        if not payload:
            return

        # 1. Normalization
        data = None

        # Retrieve the specific adapter for this payload instance
        adapter = self.adapter_registry.get_adapter_for_instance(payload)

        if adapter:
            try:
                # Try to convert the payload to a dictionary using the adapter
                data = adapter.to_dict(payload)
            except Exception as e:
                logger.warning(e, exc_info=True)
        elif isinstance(payload, dict):
            # If payload is already a dictionary, use it directly
            data = payload
        elif isinstance(payload, str):
            # Attempt to parse a JSON string
            try:
                clean_str = payload.strip()

                # Handle markdown code blocks containing JSON
                if "```json" in clean_str:
                    match = re.search(r"```json(.*?)```", clean_str, re.DOTALL)
                    if match:
                        clean_str = match.group(1).strip()
                elif "```" in clean_str:
                    match = re.search(r"```(.*?)```", clean_str, re.DOTALL)
                    if match:
                        clean_str = match.group(1).strip()

                # If the string looks like a JSON object, attempt to load it
                if clean_str.startswith("{"):
                    data = json.loads(clean_str)
            except Exception as e:
                logger.warning(e, exc_info=True)

        # 2. Matching Logic
        if not self.config.decisions:
            return

        # Case A: Payload is a dictionary (structured data)
        if isinstance(data, dict):
            for decision in self.config.decisions:
                # Check if the target field exists in the data
                if decision.target_field in data:
                    val = data[decision.target_field]
                    # Convert the value to string (handling Enums if present)
                    val_str = val.name if hasattr(val, "name") else str(val)

                    # Check if the value matches any of the expected values
                    if val_str in decision.expected_values:
                        self.registry.register_decision_hit(decision.id, val_str)

        # Case B: Payload is a string (unstructured text)
        elif isinstance(payload, str):
            clean_text = payload.strip()
            for decision in self.config.decisions:
                for expected in decision.expected_values:
                    # Check if the expected value is present in the text
                    if expected in clean_text:
                        self.registry.register_decision_hit(decision.id, expected)
