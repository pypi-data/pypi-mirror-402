"""This module provides functionality to scan and analyze data structures (Pydantic models, dataclasses) within a given codebase.

It uses an abstraction layer for the `inspect` module to improve testability and isolate the scanning process from the actual filesystem and inspection calls.
"""

import inspect
import logging
import os
import sys
import typing
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from agent_cover.config import AgentCoverConfig, DecisionConfig, get_config
from agent_cover.registry import AgentRegistry, get_registry

from .adapters import AdapterRegistry, get_default_adapter_registry

logger = logging.getLogger(__name__)

# --- ABSTRACTION LAYER FOR INSPECT ---


class InspectionProvider:
    """Helper class to abstract the calls to inspect that touch the filesystem.

    Attributes:
        None

    Methods:
        get_file(obj: Any) -> str: Returns the file path of the given object.
        get_source_lines(obj: Any) -> Tuple[List[str], int]: Returns the source code lines and starting line number of the given object.
    """

    def get_file(self, obj: Any) -> str:
        """Returns the file path of the given object.

        Args:
            obj: The object to get the file path for.

        Returns:
            The file path of the object.
        """
        return inspect.getfile(obj)

    def get_source_lines(self, obj: Any) -> Tuple[List[str], int]:
        """Returns the source code lines and starting line number of the given object.

        Args:
            obj: The object to get the source code lines for.

        Returns:
            A tuple containing the source code lines as a list of strings and the starting line number.
        """
        return inspect.getsourcelines(obj)


def _default_module_iterator() -> Dict[str, Any]:
    """Returns a dictionary of all imported modules.

    Args:
        None

    Returns:
        A dictionary where keys are module names and values are the modules themselves.
    """
    return dict(sys.modules)


def scan_pydantic_models(
    registry: Optional[AgentRegistry] = None,
    config: Optional[AgentCoverConfig] = None,
    root_path: Optional[str] = None,
    adapter_registry: Optional[AdapterRegistry] = None,
    module_iterator: Optional[Callable[[], Dict[str, Any]]] = None,
    inspector: Optional[InspectionProvider] = None,
):
    """Scans loaded modules to automatically generate Business Logic decisions.

    This function inspects Pydantic models and Dataclasses to find fields with
    finite sets of expected values. It automatically populates the
    [`AgentCoverConfig`][agent_cover.config.AgentCoverConfig] with these rules.

    Supported Types:
    - **Enum**: Expects all enum members.
    - **Literal**: Expects all literal values (e.g., `Literal["yes", "no"]`).
    - **Bool**: Expects `True` and `False`.

    Args:
        registry: The AgentRegistry instance. Defaults to the result of get_registry().
        config: The AgentCoverConfig instance. Defaults to the result of get_config().
        root_path: The root path to scan for modules. Defaults to the current working directory.
        adapter_registry: The AdapterRegistry instance. Defaults to the result of get_default_adapter_registry().
        module_iterator: A callable that returns an iterator over the modules. Defaults to _default_module_iterator.
        inspector: An instance of InspectionProvider for abstracting inspect calls. Defaults to None.

    Examples:
        If you have this model:
        ```python
        class Sentiment(BaseModel):
            label: Literal["POSITIVE", "NEGATIVE"]
        ```
        This scanner creates a Decision rule expecting both "POSITIVE" and "NEGATIVE"
        to appear in the `label` field during testing.
    """
    if registry is None:
        registry = get_registry()
    if config is None:
        config = get_config()
    if root_path is None:
        root_path = os.getcwd()
    if adapter_registry is None:
        adapter_registry = get_default_adapter_registry()
    if module_iterator is None:
        module_iterator = _default_module_iterator
    if inspector is None:
        inspector = InspectionProvider()

    existing_ids = {d.id for d in config.decisions}
    count = 0

    modules_snapshot = module_iterator()

    for mod_name, mod in modules_snapshot.items():
        if not hasattr(mod, "__file__") or not mod.__file__:
            continue
        mod_file = os.path.abspath(mod.__file__)

        # User code filter
        if not mod_file.startswith(root_path) or "site-packages" in mod_file:
            continue

        for name, val in list(vars(mod).items()):
            adapter = adapter_registry.get_adapter_for_class(val)
            if not adapter:
                continue

            try:
                # We use the injected inspector to get the file
                class_file = inspector.get_file(val)
                class_file = os.path.abspath(class_file)

                if (
                    not class_file.startswith(root_path)
                    or "site-packages" in class_file
                ):
                    continue

                try:
                    # We use the injected inspector for the lines of code
                    lines, start_line = inspector.get_source_lines(val)
                except Exception as e:
                    logger.warning(e, exc_info=True)
                    start_line = 0
            except Exception as e:
                logger.warning(e, exc_info=True)
                # If get_file fails (e.g. built-in or dynamic class without mocks), we skip
                continue

            try:
                fields_map = adapter.get_fields(val)
                _analyze_model_fields(
                    val, fields_map, config, existing_ids, class_file, start_line
                )
                count += 1
            except Exception as e:
                logger.warning(f"[AgentCover][STRUCT] Skip {name}: {e}", exc_info=True)


def _analyze_model_fields(
    cls,
    fields_map: dict,
    config: AgentCoverConfig,
    existing_ids: set,
    file_path,
    line_number,
):
    """Analyzes the fields of a model and creates decisions based on expected values.

    Args:
        cls: The class of the model.
        fields_map: A dictionary of fields and their types.
        config: The AgentCoverConfig instance.
        existing_ids: A set of existing decision IDs.
        file_path: The file path of the model.
        line_number: The line number of the model definition.
    """
    for field_name, field_type in fields_map.items():
        expected_values = []

        # Enum management
        if isinstance(field_type, type) and issubclass(field_type, Enum):
            expected_values = [e.name for e in field_type]

        # Literal management
        elif typing.get_origin(field_type) is typing.Literal:
            expected_values = [str(arg) for arg in typing.get_args(field_type)]

        # Bool management
        elif field_type is bool:
            expected_values = ["True", "False"]

        if expected_values:
            decision_id = f"{cls.__name__}.{field_name}"

            if decision_id not in existing_ids:
                logger.debug(
                    f"[AgentCover][STRUCT] Auto-discovered decision: {decision_id}"
                )

                new_decision = DecisionConfig(
                    id=decision_id,
                    description=f"Auto-generated from {cls.__name__}",
                    target_field=field_name,
                    expected_values=expected_values,
                    file_path=file_path,
                    line_number=line_number,
                )

                config.decisions.append(new_decision)
                existing_ids.add(decision_id)
