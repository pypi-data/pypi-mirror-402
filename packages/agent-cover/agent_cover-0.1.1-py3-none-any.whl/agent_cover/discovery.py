"""Module for dynamic repository exploration and module importing.

This module provides utilities to recursively walk through a directory tree,
identify Python files, and dynamically import them into the current runtime.

## 🔗 Architectural Relationships

Discovery serves as the **Pre-flight Check** or "Hydration" phase of the coverage process.
It ensures the environment is fully populated before instrumentation begins.

* **Enables:** [Static Analysis][agent_cover.instrumentation].
    Scanners like [Structures][agent_cover.instrumentation.structures] or [Raw Strings][agent_cover.instrumentation.raw_strings]
    iterate over loaded modules (`sys.modules`). Without discovery, they would only see
    files explicitly imported by your tests, missing unused code (false negatives in coverage).
* **Prepares:** [Direct Patching][agent_cover.instrumentation].
    Instrumentors need the target classes (e.g., `MyCustomTool`) to be loaded in memory
    to apply wrappers.
* **Orchestrated by:** [Plugin][agent_cover.plugin] and [SDK][agent_cover.sdk].
    Called at the very beginning of the lifecycle (`pytest_configure`).

## ⚙️ How it works

It performs a "forced import" strategy to trigger **Import-Time Side Effects** (like decorators registering tools)
without executing the actual agent logic.


Key Features:
- **Smart Filtering**: Automatically ignores `.git`, `venv`, `node_modules`, etc.
- **Safe Importing**: Catches import errors to prevent crashing the test suite if a user file is broken.
"""

import importlib.util
import logging
import os
import sys
from typing import Callable, Iterator, List, Optional, Tuple

from agent_cover.messages import InstrumentationLogger as Log

logger = logging.getLogger(__name__)


# --- DEFAULT IO WRAPPERS ---
def _default_walker(path: str) -> Iterator[Tuple[str, List[str], List[str]]]:
    """Default wrapper for `os.walk`.

    This function provides a default implementation for traversing a directory
    tree using `os.walk`. It is designed to be easily replaceable for testing
    purposes.

    Args:
        path (str): The root directory path to start the traversal from.

    Yields:
        Iterator[Tuple[str, List[str], List[str]]]: An iterator that yields tuples
            containing the current directory path, a list of subdirectory names,
            and a list of file names within the current directory.
    """
    return os.walk(path)


def _default_importer(mod_name: str, file_path: str) -> bool:
    """Default module importer using `importlib`.

    This function attempts to import a Python module from a given file path
    using `importlib.util`. It handles the module loading and execution.

    Args:
        mod_name (str): The name of the module to import.
        file_path (str): The absolute path to the Python file.

    Returns:
        bool: True if the module was successfully imported, False otherwise.
    """
    try:
        spec = importlib.util.spec_from_file_location(mod_name, file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[mod_name] = module
            spec.loader.exec_module(module)
            return True
    except Exception as e:
        Log.log_import_error(logger, file_path, e)
    return False


def discover_repository_modules(
    root_path: Optional[str] = None,
    walker_func: Optional[Callable] = None,
    importer_func: Optional[Callable] = None,
):
    """Recursively explores a directory to find Python files and force their import.

    This function performs a "Pre-flight Check" of the user's codebase. By importing
    modules found in `root_path`, it ensures that:
    1.  `@tool` decorators run and register definitions in the registry.
    2.  Global prompt variables are loaded and can be scanned.
    3.  Class definitions are available for patching.

    Args:
        root_path (Optional[str]): The root directory to start discovery.
        walker_func (Optional[Callable]): Dependency injection for file system walking (testing).
        importer_func (Optional[Callable]): Dependency injection for module importing (testing).
    """
    if root_path is None:
        root_path = os.getcwd()

    # Setup Defaults
    if walker_func is None:
        walker_func = _default_walker
    if importer_func is None:
        importer_func = _default_importer

    logger.debug(f"Starting module discovery in: {root_path}")

    IGNORE_DIRS = {
        ".git",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        ".pytest_cache",
        ".idea",
        ".vscode",
        "site-packages",
        "dist",
        "build",
        "node_modules",
    }

    discovered_count = 0

    # 1. File System Navigation (Mockable)
    for root, dirs, files in walker_func(root_path):
        # Filter directories in-place
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                full_path = os.path.join(root, file)

                try:
                    rel_path = os.path.relpath(full_path, root_path)
                    mod_name = os.path.splitext(rel_path)[0].replace(os.path.sep, ".")

                    # Avoid re-importing if already present in sys.modules
                    # (Note: in tests sys.modules can be mocked externally)
                    if mod_name in sys.modules:
                        continue

                    # 2. Import (Mockable)
                    if importer_func(mod_name, full_path):
                        discovered_count += 1

                except Exception as e:
                    logger.warning(f"Discovery Error {full_path}: {e}", exc_info=True)
                    continue

    logger.debug(
        f"Discovery finished. Forced import of {discovered_count} new modules."
    )
