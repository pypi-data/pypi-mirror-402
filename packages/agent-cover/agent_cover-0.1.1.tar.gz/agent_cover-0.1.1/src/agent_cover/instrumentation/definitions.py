"""Configuration classes for instrumentation targets."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union


@dataclass
class TargetConfig:
    """Represents the configuration for a target to be instrumented.

    This dataclass holds information about a specific target, including the module
    and class name, methods to instrument, and optional parameters and version
    constraints.

    Attributes:
        module (str): The module where the target class or function is located.
        class_name (str): The name of the class or function to instrument.
        methods (Union[Dict[str, str], List[str], None]): Methods to instrument,
            or None if not applicable. Can be a Dict (e.g., agent strategies)
            or a List (e.g., method names for prompts/tools). Defaults to None.
        params (Dict[str, Any]): Additional parameters specific to the
            instrumentor (e.g., type="render" for promptflow). Defaults to an
            empty dictionary.
        min_version (Optional[str]): Minimum version of the package required for
            instrumentation. Defaults to None.
        max_version (Optional[str]): Maximum version of the package supported
            for instrumentation. Defaults to None.

    Methods:
        from_dict: Creates a TargetConfig instance from a dictionary.
    """

    module: str
    class_name: str
    methods: Union[Dict[str, str], List[str], None] = None
    params: Dict[str, Any] = field(default_factory=dict)
    min_version: Optional[str] = None
    max_version: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Union[Dict[str, Any], "TargetConfig"]) -> "TargetConfig":
        """Creates a TargetConfig instance from a dictionary.

        This class method allows creating a TargetConfig object from a dictionary,
        handling potential type conversions and default values.

        Args:
            data (Dict[str, Any] | TargetConfig): A dictionary containing the target
                configuration data or an existing TargetConfig object.

        Returns:
            TargetConfig: A TargetConfig object initialized from the data.
        """
        if isinstance(data, cls):
            return data

        if not isinstance(data, dict):
            raise ValueError(
                f"Invalid configuration format. Expected dict or TargetConfig, got {type(data)}"
            )

        return cls(
            module=data["module"],
            class_name=data["class_name"],
            methods=data.get("methods"),
            params=data.get("params", {}),
            min_version=data.get("min_version"),
            max_version=data.get("max_version"),
        )


# Type alias for a list of targets, which can be dictionaries or TargetConfig objects.
TargetList = List[Union[Dict[str, Any], TargetConfig]]
