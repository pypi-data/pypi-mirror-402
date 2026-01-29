"""Utility module for low-level operations.

This module provides helpers for:
1.  **Time**: Testable time providers.
2.  **Safety**: Decorators that don't crash on Mock objects.
3.  **Stack Inspection**: The core logic for finding *where* a prompt or tool was defined.
"""

import functools
import inspect
import logging
import os
import time
from datetime import datetime
from typing import Any, Callable, Iterator, Optional

from agent_cover.registry import AgentRegistry, get_registry

logger = logging.getLogger(__name__)

# --- TIME PROVIDER ---


def _default_time_provider() -> float:
    """Provides the default time provider, using `time.time()`.

    This is a helper function to get the current time in seconds since the epoch.

    Returns:
        float: The current time as a float.
    """
    return time.time()


def get_timestamp(provider: Optional[Callable[[], float]] = None) -> float:
    """Gets a timestamp using the provided provider or the default time provider.

    Args:
        provider (Optional[Callable[[], float]]): An optional callable that
            provides the timestamp. If None, the default time provider is used.

    Returns:
        float: The timestamp as a float.
    """
    if provider is None:
        provider = _default_time_provider
    return provider()


def format_iso_time(timestamp: Optional[float] = None) -> str:
    """Formats a timestamp into ISO 8601 format.

    Args:
        timestamp (Optional[float]): An optional timestamp to format.
            If None, the current time is used.

    Returns:
        str: The timestamp in ISO 8601 format.
    """
    ts = timestamp if timestamp is not None else time.time()
    return datetime.fromtimestamp(ts).isoformat()


# --- SAFE WRAPS ---


def safe_wraps(original_func: Callable) -> Callable:
    """Robust alternative to functools.wraps.

    This decorator does not fail if the original object is an incomplete Mock
    (common in tests). It preserves the original function's metadata
    (name, docstring, etc.) when wrapping a function. It handles cases
    where the original function might be a Mock object that doesn't
    fully implement the attributes expected by functools.wraps.

    Args:
        original_func (Callable): The original function to wrap.

    Returns:
        Callable: A decorator that, when applied to a wrapper function, sets
        the wrapper's attributes to match the original function's.
    """

    def decorator(wrapper: Callable) -> Callable:
        """The decorator function.

        Args:
            wrapper (Callable): The wrapper function.

        Returns:
            Callable: The wrapped function with preserved metadata.
        """
        try:
            # Apply standard wraps. Note: In Python 3.12+, wraps may suppress
            # AttributeError internally if attributes are missing on original_func.
            wrapper = functools.wraps(original_func)(wrapper)

            # Explicitly check if critical attributes are accessible.
            # If original_func raises AttributeError here (e.g., a Broken Mock),
            # we force an exception to trigger the fallback block below.
            _ = original_func.__name__

            return wrapper
        except (AttributeError, ValueError):
            # Manual fallback for Mock objects that don't have __name__ etc.
            # We use getattr with default because accessing __name__ directly might raise.
            wrapper.__name__ = getattr(
                original_func, "__name__", "mock_wrapper"
            )  # Set name
            wrapper.__doc__ = getattr(original_func, "__doc__", "")  # Set docstring
            return wrapper

    return decorator


# --- STACK INSPECTION & MOCKING ---


class FrameInterface:
    """Mock Helper for tests: simulates a stack frame.

    This class provides a mock implementation of a Python stack frame,
    allowing tests to simulate call stacks without executing actual code.

    Attributes:
        filename (str): The filename of the code.
        lineno (int): The line number.
        lasti (int): The last instruction index.
        globals_dict (dict): A dictionary of global variables.
        _back (Optional[Any]): The previous frame (simulating the call stack).
    """

    def __init__(
        self, filename: str, lineno: int, lasti: int, globals_dict: dict, back=None
    ):
        """Initializes a FrameInterface object.

        Used for mocking stack frames in tests.

        Args:
            filename (str): The filename of the code.
            lineno (int): The line number.
            lasti (int): The last instruction index.
            globals_dict (dict): A dictionary of global variables.
            back (Optional[Any]): The previous frame. Defaults to None.
        """
        self.filename = filename
        self.lineno = lineno
        self.lasti = lasti
        self.globals_dict = globals_dict
        self._back = back

    @property
    def f_code(self):
        """Returns a mock f_code object.

        Required to simulate a stack frame structure expected by inspect module.

        Returns:
            object: A mock Code object with a co_filename attribute.
        """

        class Code:
            def __init__(self, fname):
                self.co_filename = fname

        return Code(self.filename)

    @property
    def f_lineno(self):
        """int: The line number of the frame."""
        return self.lineno

    @property
    def f_lasti(self):
        """int: The index of the last instruction executed."""
        return self.lasti

    @property
    def f_globals(self):
        """dict: The global variables dictionary of the frame."""
        return self.globals_dict

    @property
    def f_back(self):
        """Optional[Any]: The previous stack frame."""
        return self._back


def _default_frame_walker(start_frame=None) -> Iterator[Any]:
    """Generator that navigates the real stack.

    This function is used to traverse the call stack. It starts from the
    current frame or a specified starting frame and yields each frame in
    the stack until the end is reached.

    Args:
        start_frame (Optional[Any]): An optional starting frame. If None,
            the current frame is used.

    Yields:
        Any: Each frame in the stack.
    """
    current = start_frame or inspect.currentframe()
    if not start_frame and current:
        current = current.f_back  # Skip the current frame itself

    while current:
        yield current
        current = current.f_back


def _default_internal_filter(filename: str, lib_path: str) -> bool:
    """Default filter for internal files.

    This function checks if a filename should be considered internal to the
    instrumentation library. It filters out files from the standard library,
    pytest, and site-packages.

    Args:
        filename (str): The filename to check.
        lib_path (str): The path to the instrumentation library.

    Returns:
        bool: True if the file is internal, False otherwise.
    """
    filename = os.path.normpath(filename)
    lib_path = os.path.normpath(lib_path)

    return (
        lib_path in filename
        or os.sep + "_pytest" + os.sep in filename
        or os.sep + "site-packages" + os.sep in filename
        or filename.startswith("<")
    )


def get_definition_location(
    registry: Optional[AgentRegistry] = None,
    start_frame: Optional[Any] = None,
    root_path: Optional[str] = None,
    internal_filter: Optional[Callable[[str, str], bool]] = None,
    stack_walker: Optional[Callable[[Any], Iterator[Any]]] = None,
) -> str:
    """Determines the source file and line number of the caller.

    It traverses the Python call stack backwards to find the first frame that
    belongs to the user's codebase (ignoring internal AgentCover frames and
    external libraries).

    Args:
        registry (Optional[AgentRegistry]): The AgentRegistry instance.
            If None, retrieves the global registry.
        start_frame (Optional[Any]): An optional starting frame.
        root_path (Optional[str]): The root path of the project.
            If None, uses the current working directory.
        internal_filter (Optional[Callable[[str, str], bool]]): An optional
            filter function for internal files. Defaults to _default_internal_filter.
        stack_walker (Optional[Callable[[Any], Iterator[Any]]]): A callable
            used to walk the stack. Defaults to _default_frame_walker.

    Returns:
        str: A string representing the definition location (e.g., "file.py:123")
        or "unknown:0" if the location cannot be determined.
    """
    if registry is None:
        registry = get_registry()
    if root_path is None:
        root_path = os.getcwd()
    if internal_filter is None:
        internal_filter = _default_internal_filter
    if stack_walker is None:
        stack_walker = _default_frame_walker

    lib_path = os.path.dirname(os.path.abspath(__file__))

    # Navigate the stack (real or mocked)
    for frame in stack_walker(start_frame):
        # Robust support for incomplete MockFrames or real frame objects
        filename = "unknown"
        if hasattr(frame, "f_code") and hasattr(frame.f_code, "co_filename"):
            filename = frame.f_code.co_filename
        elif hasattr(frame, "filename"):  # Fallback for simple Mocks
            filename = frame.filename

        try:
            abs_path = os.path.abspath(filename)
        except Exception as e:
            logger.warning(e, exc_info=True)
            abs_path = str(filename)

        f_globals = getattr(frame, "f_globals", {})

        is_internal = f_globals.get("__name__") == __name__ or internal_filter(
            abs_path, lib_path
        )

        if not is_internal:
            if abs_path.startswith(root_path):
                lineno = getattr(frame, "f_lineno", 0)
                lasti = getattr(frame, "f_lasti", 0)

                instruction_id = (abs_path, lineno, lasti)

                if instruction_id in registry.instruction_map:
                    return registry.instruction_map[instruction_id]

                base_key = f"{abs_path}:{lineno}"
                count = registry.counters.get(base_key, 0) + 1
                registry.counters[base_key] = count

                final_key = f"{base_key}#{count}" if count > 1 else base_key
                registry.instruction_map[instruction_id] = final_key

                return final_key

    return "unknown:0"


def _get_nested_attr(obj: Any, path: str) -> Optional[Any]:
    """Retrieves an attribute using dot notation (e.g. 'metadata.name')."""
    try:
        for part in path.split("."):
            obj = getattr(obj, part)
        return obj
    except AttributeError:
        return None
