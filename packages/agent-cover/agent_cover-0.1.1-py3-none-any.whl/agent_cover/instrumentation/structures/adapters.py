"""Module for converting data structures to dictionaries.

This module provides adapters for converting different data structures
(e.g., Pydantic models, dataclasses) into dictionaries. These adapters
enable AgentCover to process data from various sources in a unified
manner.
"""

from abc import ABC, abstractmethod
from dataclasses import asdict, is_dataclass
from typing import Any, Optional


# --- INTERFACCIA BASE ---
class StructureAdapter(ABC):
    """Abstract base class for structure adapters.

    Structure adapters are responsible for converting objects of different
    types into dictionaries, enabling unified handling of various data
    structures within the AgentCover framework.

    Attributes:
        None

    Methods:
        can_handle_class(cls: type) -> bool:
            Abstract method to check if the adapter can handle a given class.
        can_handle_instance(obj: Any) -> bool:
            Abstract method to check if the adapter can handle a given instance.
        get_fields(cls: type) -> dict[str, type]:
            Abstract method to retrieve the fields of a class.
        to_dict(obj: Any) -> dict:
            Abstract method to convert an object to a dictionary.
    """

    @abstractmethod
    def can_handle_class(self, cls: type) -> bool:
        """Checks if this adapter can handle the given class.

        Args:
            cls: The class to check.

        Returns:
            True if the adapter can handle the class, False otherwise.
        """
        pass

    @abstractmethod
    def can_handle_instance(self, obj: Any) -> bool:
        """Checks if this adapter can handle the given instance.

        Args:
            obj: The instance to check.

        Returns:
            True if the adapter can handle the instance, False otherwise.
        """
        pass

    @abstractmethod
    def get_fields(self, cls: type) -> dict[str, type]:
        """Retrieves the fields of the given class.

        Args:
            cls: The class to inspect.

        Returns:
            A dictionary where keys are field names and values are field types.
        """
        pass

    @abstractmethod
    def to_dict(self, obj: Any) -> dict:
        """Converts the given object to a dictionary.

        Args:
            obj: The object to convert.

        Returns:
            A dictionary representation of the object.
        """
        pass


# --- IMPLEMENTAZIONI ---
class PydanticAdapter(StructureAdapter):
    """Adapter for Pydantic models.

    This adapter is designed to convert Pydantic models into dictionaries,
    allowing AgentCover to analyze and process data from Pydantic-based
    data structures. It supports both Pydantic V1 and V2.

    Attributes:
        BaseModel: The Pydantic BaseModel class (dynamically imported).

    Methods:
        can_handle_class(cls: type) -> bool:
            Checks if the adapter can handle a given class.
        can_handle_instance(obj: Any) -> bool:
            Checks if the adapter can handle a given instance.
        get_fields(cls: type) -> dict[str, type]:
            Retrieves the fields of a class.
        to_dict(obj: Any) -> dict:
            Converts a Pydantic model instance to a dictionary.
    """

    def __init__(self, pydantic_module: Any = None):
        """Initializes a PydanticAdapter instance.

        Args:
            pydantic_module:  Optional. Dependency Injection of the pydantic module.
                If None, attempts to import it. If passed (e.g., Mock), uses that.
        """
        self.BaseModel = None

        if pydantic_module:
            # Test Case: Using the injected mocked module
            self.BaseModel = getattr(pydantic_module, "BaseModel", None)
        else:
            # Runtime Case: Let's try the real import
            try:
                import pydantic

                self.BaseModel = pydantic.BaseModel
            except ImportError:
                pass

    def can_handle_class(self, cls: type) -> bool:
        """Checks if the given class is a Pydantic model.

        Args:
            cls: The class to check.

        Returns:
            True if the class is a Pydantic model, False otherwise.
        """
        if self.BaseModel is None:
            return False
        # Robust verification to avoid false positives with mocks
        try:
            return (
                isinstance(cls, type)
                and issubclass(cls, self.BaseModel)
                and cls is not self.BaseModel
            )
        except TypeError:
            return False

    def can_handle_instance(self, obj: Any) -> bool:
        """Checks if the given object is an instance of a Pydantic model.

        Args:
            obj: The object to check.

        Returns:
            True if the object is a Pydantic model instance, False otherwise.
        """
        if self.BaseModel is None:
            return False
        return isinstance(obj, self.BaseModel)

    def get_fields(self, cls: type) -> dict[str, Any]:
        """Retrieves the fields of a Pydantic model.

        Args:
            cls: The Pydantic model class.

        Returns:
            A dictionary of field names and types.
        """
        # Dual V1/V2 support
        fields_info = getattr(cls, "model_fields", None)  # Pydantic V2
        if fields_info is None:
            fields_info = getattr(cls, "__fields__", {})  # Pydantic V1

        extracted = {}
        for name, info in fields_info.items():
            # In V1 info.type_, in V2 info.annotation
            extracted[name] = getattr(info, "annotation", getattr(info, "type_", None))
        return extracted

    def to_dict(self, obj: Any) -> dict:
        """Converts a Pydantic model instance to a dictionary.

        Args:
            obj: The Pydantic model instance.

        Returns:
            A dictionary representation of the Pydantic model.
        """
        # Dual V1/V2 dump support
        if hasattr(obj, "model_dump"):
            return obj.model_dump()  # V2
        if hasattr(obj, "dict"):
            return obj.dict()  # V1
        return {}


class DataclassAdapter(StructureAdapter):
    """Adapter for dataclasses.

    This adapter is designed to convert dataclasses into dictionaries,
    allowing AgentCover to analyze and process data from dataclass-based
    data structures.

    Attributes:
        None

    Methods:
        can_handle_class(cls: type) -> bool:
            Checks if the adapter can handle a given class.
        can_handle_instance(obj: Any) -> bool:
            Checks if the adapter can handle a given instance.
        get_fields(cls: type) -> dict[str, type]:
            Retrieves the fields of a class.
        to_dict(obj: Any) -> dict:
            Converts a dataclass instance to a dictionary.
    """

    def can_handle_class(self, cls: type) -> bool:
        """Checks if the given class is a dataclass.

        Args:
            cls: The class to check.

        Returns:
            True if the class is a dataclass, False otherwise.
        """
        return isinstance(cls, type) and is_dataclass(cls)

    def can_handle_instance(self, obj: Any) -> bool:
        """Checks if the given object is an instance of a dataclass.

        Args:
            obj: The object to check.

        Returns:
            True if the object is a dataclass instance, False otherwise.
        """
        return is_dataclass(obj) and not isinstance(obj, type)

    def get_fields(self, cls: type) -> dict[str, Any]:
        """Retrieves the fields of a dataclass.

        Args:
            cls: The dataclass class.

        Returns:
            A dictionary of field names and types.
        """
        return getattr(cls, "__annotations__", {})

    def to_dict(self, obj: Any) -> dict:
        """Converts a dataclass instance to a dictionary.

        Args:
            obj: The dataclass instance.

        Returns:
            A dictionary representation of the dataclass.
        """
        return asdict(obj)


# --- CLASS REGISTRY ---


class AdapterRegistry:
    """Registry for managing structure adapters.

    This registry stores and provides access to different structure adapters,
    allowing AgentCover to handle various data structures uniformly.

    Attributes:
        _adapters: A list of StructureAdapter instances.

    Methods:
        register(adapter: StructureAdapter):
            Registers a new adapter.
        clear():
            Clears all registered adapters.
        get_adapter_for_class(cls: type) -> Optional[StructureAdapter]:
            Retrieves the adapter for a given class.
        get_adapter_for_instance(obj: Any) -> Optional[StructureAdapter]:
            Retrieves the adapter for a given instance.
    """

    def __init__(self):
        """Initializes a new AdapterRegistry instance."""
        self._adapters: list[StructureAdapter] = [
            PydanticAdapter(),
            DataclassAdapter(),
        ]

    def register(self, adapter: StructureAdapter):
        """Registers a new structure adapter.

        Args:
            adapter: The StructureAdapter instance to register.
        """
        self._adapters.insert(0, adapter)

    def clear(self):
        """Clears all registered adapters."""
        self._adapters = []

    def get_adapter_for_class(self, cls: type) -> Optional[StructureAdapter]:
        """Retrieves the adapter for a given class.

        Args:
            cls: The class to find an adapter for.

        Returns:
            The StructureAdapter instance that can handle the class, or None.
        """
        for adapter in self._adapters:
            if adapter.can_handle_class(cls):
                return adapter
        return None

    def get_adapter_for_instance(self, obj: Any) -> Optional[StructureAdapter]:
        """Retrieves the adapter for a given instance.

        Args:
            obj: The instance to find an adapter for.

        Returns:
            The StructureAdapter instance that can handle the instance, or None.
        """
        for adapter in self._adapters:
            if adapter.can_handle_instance(obj):
                return adapter
        return None


# Default singleton
_default_adapter_registry = AdapterRegistry()


def get_default_adapter_registry():
    """Retrieves the default AdapterRegistry instance.

    Returns:
        The default AdapterRegistry instance.
    """
    return _default_adapter_registry
