"""Configuration management module for AgentCover.

This module acts as the schema definition for the `agent-cover.yaml` file.
It dictates how the library understands the user's business requirements ("Decisions").

## The `agent-cover.yaml` File

This file defines the **Business Logic** decisions you want to enforce manually.
Place it in the root of your project (where you run pytest).

```yaml
decisions:
  - id: "OrderProcessor.status"        # Unique ID for the rule
    description: "Check order flow"    # Description for the report
    target_field: "status"             # JSON key to look for in LLM output
    expected_values:                   # Values required for 100% coverage
      - "PENDING"
      - "SHIPPED"
      - "CANCELLED"

  - id: "SentimentAnalysis"
    target_field: "sentiment"
    expected_values: ["POSITIVE", "NEGATIVE", "NEUTRAL"]

## 🔗 Architectural Relationships

The configuration serves as the **Rulebook** for the coverage session.

* **Consumed by:** [OutputAnalyzer][agent_cover.instrumentation.analyzer.OutputAnalyzer].
    The analyzer reads the `decisions` list defined here to validate runtime LLM outputs against expected values.
* **Populated by:**
    1.  **YAML Loader:** (User defined rules in `agent-cover.yaml`).
    2.  **[Structure Scanner][agent_cover.instrumentation.structures.scanner.scan_pydantic_models]:** (Auto-generated rules found by inspecting Pydantic models).

Key Components:
    - **[DecisionConfig][agent_cover.config.DecisionConfig]**: Represents a single business rule.
    - **[AgentCoverConfig][agent_cover.config.AgentCoverConfig]**: The root configuration container.
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class DecisionConfig:
    """Represents a configuration for a specific decision within the agent.

    This dataclass defines a "Decision Coverage" goal. It maps a specific field
    in the agent's output to a set of expected values that must be observed
    to achieve 100% coverage.

    Attributes:
        id (str): Unique identifier for this decision (e.g., "SentimentAnalysis" or "ClassName.field").
        description (str): Human-readable description of what this rule tests.
        target_field (str): The key in the JSON output/dict to inspect (e.g., "status", "intent").
        expected_values (List[str]): All possible values that *should* be observed during testing.
        file_path (Optional[str]): Source file origin (auto-filled by scanners).
        line_number (Optional[int]): Source line origin (auto-filled by scanners).

    Examples:
        Defining a rule to check if the agent handles both 'Refund' and 'Sales' intents:

        ```yaml
        # In agent-cover.yaml
        decisions:
          - id: intent_classification
            description: Ensure all intents are triggered
            target_field: intent
            expected_values:
              - REFUND
              - SALES
              - TECH_SUPPORT
        ```
    """

    id: str
    description: str
    target_field: str  # The JSON field to search for (e.g., "intent")
    expected_values: List[
        str
    ]  # The values we expect to see (e.g., ["SALES", "SUPPORT"])
    file_path: Optional[str] = None
    line_number: Optional[int] = 0


@dataclass
class AgentCoverConfig:
    """The root configuration object for AgentCover.

    This dataclass holds the global configuration, primarily the list of
    business logic rules ([DecisionConfig][agent_cover.config.DecisionConfig])
    that the [OutputAnalyzer][agent_cover.instrumentation.analyzer.OutputAnalyzer]
    will use.

    Attributes:
        decisions (List[DecisionConfig]): A list of decision rules to enforce.
    """

    decisions: List[DecisionConfig] = field(default_factory=list)


# Global singleton
_config: Optional[AgentCoverConfig] = None

# --- DEFAULT IO HELPERS ---


def _default_file_reader(path: str) -> Dict[str, Any]:
    """Default file reader function.

    Reads a YAML file from the given path and returns its content as a
    dictionary. If the file does not exist, it returns an empty dictionary.

    Args:
        path (str): The path to the YAML file.

    Returns:
        Dict[str, Any]: A dictionary representing the YAML content, or an empty
            dictionary if the file does not exist or is empty.
    """
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def parse_config_from_dict(data: Dict[str, Any]) -> AgentCoverConfig:
    """Parses configuration data from a dictionary.

    This function takes a dictionary containing configuration data and
    parses it into an AgentCoverConfig object.

    Args:
        data (Dict[str, Any]): A dictionary containing the configuration data.

    Returns:
        AgentCoverConfig: An AgentCoverConfig object populated with the parsed data.
    """
    decisions = []
    for d in data.get("decisions", []):
        decisions.append(
            DecisionConfig(
                id=d.get("id"),
                description=d.get("description", ""),
                target_field=d.get("target_field"),
                expected_values=d.get("expected_values", []),
            )
        )
    return AgentCoverConfig(decisions=decisions)


def load_config(
    root_path: str, reader_func: Optional[Callable[[str], Dict[str, Any]]] = None
) -> AgentCoverConfig:
    """Loads the configuration from the file system.

    This function loads the AgentCover configuration from a YAML file
    (agent-cover.yaml) located in the specified root path. It uses a
    provided reader function (or a default one) to read the file content
    and then parses it into an AgentCoverConfig object.

    Args:
        root_path (str): The root path where the agent-cover.yaml file is located.
        reader_func (Optional[Callable[[str], Dict[str, Any]]]): An optional function
            to read the YAML file. This is useful for testing, allowing a mock
            reader to be injected. Defaults to None.

    Returns:
        AgentCoverConfig: An AgentCoverConfig object containing the loaded configuration.
    """
    global _config

    if reader_func is None:
        reader_func = _default_file_reader

    config_path = os.path.join(root_path, "agent-cover.yaml")
    new_config = AgentCoverConfig()

    try:
        # Here, in tests, reader_func can return a static dict without touching the disk
        data = reader_func(config_path)
        new_config = parse_config_from_dict(data)

        if new_config.decisions:
            logger.info(
                f"Loaded configuration with {len(new_config.decisions)} decision paths."
            )

    except Exception as e:
        logger.warning(f"Error loading config: {e}")

    _config = new_config
    return new_config


def get_config() -> AgentCoverConfig:
    """Retrieves the global AgentCoverConfig instance.

    This function returns the global AgentCoverConfig instance, loading it
    if it hasn't been loaded yet.

    Returns:
        AgentCoverConfig: The global AgentCoverConfig instance.
    """
    global _config
    if _config is None:
        _config = AgentCoverConfig()
    return _config
