"""Base abstractions and utilities for the agent instrumentation library.

This module defines the foundational classes that allow AgentCover to modify
third-party libraries (like LangChain or LlamaIndex) safely.

Core Concepts:
    - **BaseInstrumentor**: The blueprint for any strategy that wants to track
      code execution. It handles dependency checking (versions) and the
      apply/revert lifecycle.
    - **PatchManager**: A safety layer ensuring that:
        1. We never patch the same method twice (idempotency).
        2. We can always restore the original method (cleanup).
        3. Wrappers act transparently to the original code.

    - **TargetConfig**: Defines *what* to patch (Module + Class + Method).
"""

import importlib
import importlib.metadata
import logging
import sys
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from packaging.version import parse as parse_version

from agent_cover.context import (  # Imports for managing the agent's context
    AgentContextManager,
    get_global_context_manager,
)
from agent_cover.instrumentation.definitions import (  # Imports for target definitions
    TargetConfig,
    TargetList,
)
from agent_cover.registry import (  # Imports for interacting with the coverage registry
    AgentRegistry,
    get_registry,
)

# Logger for this module
logger = logging.getLogger(__name__)


# --- PATCH MANAGER ABSTRACTION ---
class PatchManager(ABC):
    """Abstract base class for patch managers.

    Patch managers are responsible for applying and restoring patches
    to methods and classes safely.

    Attributes:
        None

    Methods:
        apply_patch: Applies a patch to a target object.
        restore_patch: Restores a patch to a target object.
    """

    @abstractmethod
    def apply_patch(self, target_obj: Any, attribute_name: str, wrapper: Any) -> Any:
        """Applies a patch to a target object.

        Args:
            target_obj: The object to patch.
            attribute_name: The name of the attribute to patch (e.g., method name).
            wrapper: The wrapper function to apply.

        Returns:
            The original value of the attribute before the patch was applied.
        """
        pass

    @abstractmethod
    def restore_patch(self, target_obj: Any, attribute_name: str, original: Any):
        """Restores a patch to a target object.

        Args:
            target_obj: The object to restore the patch on.
            attribute_name: The name of the attribute that was patched.
            original: The original value of the attribute before the patch was applied.
        """
        pass


class DefaultPatchManager(PatchManager):
    """The default implementation of the PatchManager.

    This class applies patches by setting the attribute on the target object
    to the wrapper function. It also keeps track of patched methods to avoid
    double patching and to enable restoration.

    Attributes:
        None

    Methods:
        apply_patch: Applies a patch, marking the wrapper to prevent re-patching.
        restore_patch: Restores the original attribute value.
    """

    def apply_patch(self, target_obj: Any, attribute_name: str, wrapper: Any) -> Any:
        """Applies a patch to a target object.

        Args:
            target_obj: The object to patch.
            attribute_name: The name of the attribute to patch.
            wrapper: The wrapper function.

        Returns:
            The original method. Returns the original method immediately if
            the object is already patched.
        """
        original = getattr(target_obj, attribute_name)  # Get the original method
        if getattr(original, "_ac_patched", False):  # Check if already patched
            return original  # Return original if already patched

        wrapper._ac_patched = (
            True  # Mark wrapper as patched to prevent future patching.
        )
        setattr(target_obj, attribute_name, wrapper)  # Apply the patch
        return original  # Return the original method

    def restore_patch(self, target_obj: Any, attribute_name: str, original: Any):
        """Restores a patch to a target object.

        Args:
            target_obj: The object to restore the patch on.
            attribute_name: The name of the attribute.
            original: The original method.
        """
        current = getattr(target_obj, attribute_name, None)  # Get the current method
        if getattr(current, "_ac_patched", False):  # Check if patched
            setattr(target_obj, attribute_name, original)  # Restore original method


# --- VERSION CHECKER STRATEGY ---
class VersionChecker:
    """Abstract base class for version checkers.

    Version checkers are used to determine if a package meets certain
    version requirements before applying instrumentation.

    Attributes:
        None

    Methods:
        get_version: Retrieves the installed version of a package.
    """

    def get_version(self, package_name: str) -> Optional[str]:
        """Gets the version of a package.

        Args:
            package_name: The name of the package.

        Returns:
            The version string, or None if the package is not found.
        """
        raise NotImplementedError


class DefaultVersionChecker(VersionChecker):
    """The default implementation of the VersionChecker.

    This class uses importlib.metadata to get the version of a package.

    Attributes:
        None

    Methods:
        get_version: Retrieves the version using importlib.metadata.
    """

    def get_version(self, package_name: str) -> Optional[str]:
        """Gets the version of a package.

        Args:
            package_name: The name of the package.

        Returns:
            The version string, or None if the package is not found.
        """
        try:
            return importlib.metadata.version(package_name)
        except importlib.metadata.PackageNotFoundError:
            return None


class MockVersionChecker(VersionChecker):
    """A mock implementation of the VersionChecker for testing purposes.

    This class allows you to provide a predefined mapping of package names
    to versions.

    Attributes:
        version_map: A dictionary mapping package names to version strings.

    Methods:
        get_version: Retrieves the version from the internal map.
    """

    def __init__(self, version_map: Dict[str, str]):
        """Initializes the MockVersionChecker.

        Args:
            version_map: A dictionary mapping package names to versions.
        """
        self.version_map = version_map

    def get_version(self, package_name: str) -> Optional[str]:
        """Gets the version of a package from the version map.

        Args:
            package_name: The name of the package.

        Returns:
            The version string, or None if the package is not found in the map.
        """
        return self.version_map.get(package_name)


# --- HELPERS ---
def _default_module_iterator() -> Dict[str, Any]:
    """Provides a default module iterator.

    This function returns a dictionary of all loaded modules in the current
    Python environment. This allows for the instrumentation code to discover
    and interact with the existing modules.

    Returns:
        A dictionary where keys are module names and values are the module objects.
    """
    return dict(sys.modules)


def _default_importer(mod_name: str) -> Any:
    """Provides a default module importer.

    This function imports a module by its name using importlib.import_module.

    Args:
        mod_name: The name of the module to import.

    Returns:
        The imported module object.
    """
    return importlib.import_module(mod_name)


# --- BASE INSTRUMENTOR ---
class BaseInstrumentor(ABC):
    """Abstract base class for all instrumentation strategies.

    Subclasses (e.g., `PromptInstrumentor`, `ToolInstrumentor`) implement the
    `instrument()` method to apply specific logic. This base class provides
    the infrastructure for:
    - **Safe Patching**: Using `_safe_patch` to wrap methods without breaking them.
    - **Version Compatibility**: Using `VersionChecker` to skip instrumentation
      if the installed library version is unsupported.
    - **Module Discovery**: Finding the target modules in memory using `module_iterator`.
    """

    def __init__(
        self,
        registry: Optional[AgentRegistry] = None,
        context_manager: Optional[AgentContextManager] = None,
        patch_manager: Optional[PatchManager] = None,
        module_iterator: Optional[Callable[[], Dict[str, Any]]] = None,
        importer_func: Optional[Callable[[str], Any]] = None,
        version_checker: Union[
            VersionChecker, Callable[[str], Optional[str]], None
        ] = None,
    ):
        """Initializes the BaseInstrumentor.

        Args:
            registry: The AgentRegistry instance. Defaults to global registry if None.
            context_manager: The AgentContextManager. Defaults to global manager if None.
            patch_manager: The PatchManager. Defaults to DefaultPatchManager if None.
            module_iterator: A callable to iterate through modules. Defaults to sys.modules.
            importer_func: A function to import modules. Defaults to importlib.import_module.
            version_checker: A VersionChecker instance or a callable that returns a version string.
        """
        self.registry = (
            registry or get_registry()
        )  # Use provided registry or get the default
        self.context_manager = (
            context_manager or get_global_context_manager()
        )  # Use provided context manager or get the default
        self.patch_manager = (
            patch_manager or DefaultPatchManager()
        )  # Use provided patch manager or the default
        self.module_iterator = (
            module_iterator or _default_module_iterator
        )  # Use provided module iterator or the default
        self.importer = (
            importer_func or _default_importer
        )  # Use provided importer function or the default

        # Instance-specific logger (inherits the child class name)
        self.logger = logging.getLogger(
            self.__class__.__module__ + "." + self.__class__.__name__
        )

        # Setup Version Checker
        self.version_checker: VersionChecker
        if version_checker is None:
            self.version_checker = (
                DefaultVersionChecker()
            )  # Use default version checker if none is provided
        elif isinstance(version_checker, VersionChecker):
            self.version_checker = version_checker  # Use provided version checker
        else:
            # Backward compatibility wrapper
            class FuncWrapper(VersionChecker):
                def __init__(self, f):
                    self.f = f

                def get_version(self, p):
                    return self.f(p)

            self.version_checker = FuncWrapper(
                version_checker
            )  # Wrap the callable in a VersionChecker

        self.original_methods: Dict[
            str, Tuple[Any, str, Any]
        ] = {}  # Dictionary to store original methods before patching
        self.is_instrumented = False  # Flag to indicate if the instrumentor is active

    def _should_instrument(self, target: TargetConfig) -> bool:
        """Checks if a target should be instrumented based on version requirements.

        Args:
            target: The TargetConfig object containing version constraints.

        Returns:
            True if the target should be instrumented, False otherwise.
        """
        root_package = target.module.split(".")[0]  # Get the root package name
        installed_version_str = self.version_checker.get_version(
            root_package
        )  # Get the installed version

        if not installed_version_str:  # If version cannot be determined, instrument
            return True

        try:
            installed_version = parse_version(
                installed_version_str
            )  # Parse installed version
            if target.min_version and installed_version < parse_version(
                target.min_version
            ):
                self.logger.debug(
                    f"Skipping {target.module}: version {installed_version} < min {target.min_version}"
                )
                return False  # Skip if version is less than the minimum required
            if target.max_version and installed_version >= parse_version(
                target.max_version
            ):
                self.logger.debug(
                    f"Skipping {target.module}: version {installed_version} >= max {target.max_version}"
                )
                return False  # Skip if version is greater than or equal to the maximum allowed
        except Exception as e:
            self.logger.debug(f"Version check error for {target.module}: {e}")
            pass  # If version check fails, proceed with instrumentation

        return True  # Instrument if all checks pass

    def _normalize_targets(self, raw_targets: TargetList) -> List[TargetConfig]:
        """Normalizes raw target configurations into TargetConfig objects.

        This method converts raw target dictionaries into TargetConfig objects,
        handling potential errors during the conversion.

        Args:
            raw_targets: A list of raw target dictionaries.

        Returns:
            A list of TargetConfig objects.
        """
        normalized = []
        for t in raw_targets:
            try:
                normalized.append(TargetConfig.from_dict(t))
            except Exception as e:
                logger.warning(e, exc_info=True)
                continue  # Skip targets that fail to convert
        return normalized

    def _resolve_target_class(self, module: Any, class_path: str) -> Optional[Any]:
        """Resolves a class path within a module.

        This method traverses a module hierarchy to locate a class by its
        fully qualified name (e.g., 'package.module.ClassName').

        Args:
            module: The module object.
            class_path: The fully qualified class name (e.g., 'ClassName' or 'module.ClassName').

        Returns:
            The class object if found, otherwise None.
        """
        current = module
        parts = class_path.split(".")  # Split the class path into parts
        for part in parts:  # Iterate through the parts
            if not hasattr(current, part):  # Check if the part exists as an attribute
                return None  # Return None if the attribute does not exist
            current = getattr(current, part)  # Get the attribute
        return current  # Return the class

    @abstractmethod
    def instrument(self):
        """Abstract method for instrumenting the code.

        Subclasses must implement this method to perform the actual
        instrumentation logic.
        """
        pass

    def uninstrument(self):
        """Uninstruments the code by restoring the original methods.

        This method iterates through the patched methods and restores them
        to their original state using the PatchManager.
        """
        if not self.is_instrumented:
            return  # Do nothing if not instrumented

        # Iterate in reverse to avoid dependency issues during unpatching
        for key, (obj, name, original) in reversed(list(self.original_methods.items())):
            try:
                self.patch_manager.restore_patch(
                    obj, name, original
                )  # Restore the original method
            except Exception as e:
                self.logger.warning(f"Error unpatching {key}: {e}")  # Log any errors
        self.original_methods.clear()  # Clear the dictionary of original methods
        self.is_instrumented = False  # Set instrumentation flag to False

    def _safe_patch(self, obj: Any, method_name: str, wrapper: Any):
        """Applies a patch to a method safely.

        This method checks if a method exists and is not already patched before
        applying the patch.

        Args:
            obj: The object containing the method.
            method_name: The name of the method to patch.
            wrapper: The wrapper function.
        """
        if not hasattr(obj, method_name):
            return  # If the method doesn't exist, return
        original = getattr(obj, method_name)  # Get the original method

        if getattr(original, "_ac_patched", False):
            return  # If already patched, return

        try:
            key_name = getattr(
                obj, "__name__", str(id(obj))
            )  # Get the name of the object
            key_module = getattr(
                obj, "__module__", "unknown"
            )  # Get the module of the object
        except Exception as e:
            logger.warning(e, exc_info=True)
            key_name, key_module = (
                "unknown",
                "unknown",
            )  # Fallback if name/module retrieval fails

        key = f"{key_module}.{key_name}.{method_name}"  # Create a unique key for the method
        self.original_methods[key] = (
            obj,
            method_name,
            original,
        )  # Store the original method
        self.patch_manager.apply_patch(obj, method_name, wrapper)  # Apply the patch

    def __enter__(self):
        """Enters the instrumentation context (used with 'with' statements).

        This method calls the instrument method to apply patches.

        Returns:
            The instrumentor instance.
        """
        self.instrument()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exits the instrumentation context (used with 'with' statements).

        This method calls the uninstrument method to restore original functionality.

        Args:
            exc_type: The exception type (if any).
            exc_val: The exception value (if any).
            exc_tb: The traceback (if any).
        """
        self.uninstrument()  # Uninstrument the code
