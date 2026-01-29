"""PromptFlow Integration Module.

This module provides functionality to scan directories for PromptFlow definitions
(specifically `flow.dag.yaml` files) and register associated Jinja2 templates
into the AgentRegistry.

It supports dependency injection for file system operations to facilitate testing
without accessing the actual file system.
"""

import logging
import os
from typing import Callable, Iterator, List, Optional, Tuple

import yaml

from agent_cover.registry import AgentRegistry, get_registry

logger = logging.getLogger(__name__)

# --- DEFAULT IO HELPERS ---


def _default_walker(path: str) -> Iterator[Tuple[str, List[str], List[str]]]:
    """Default file system walker using os.walk.

    Args:
        path: The root directory path to start walking from.

    Returns:
        An iterator yielding tuples of (root, dirs, files).
    """
    return os.walk(path)


def _default_file_reader(path: str) -> str:
    """Default file reader.

    Args:
        path: The file path to read.

    Returns:
        The content of the file as a string.

    Raises:
        IOError: If the file cannot be opened or read.
    """
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def scan_promptflow_definitions(
    root_path: Optional[str] = None,
    registry: Optional[AgentRegistry] = None,
    walker_func: Optional[Callable] = None,
    file_reader: Optional[Callable] = None,
):
    """Scans for PromptFlow YAML files.

    This function scans the directory tree for `flow.dag.yaml` files and processes
    them to register Jinja2 templates found within the nodes. It is completely
    isolated from the real file system via `walker_func` and `file_reader` injections.

    Args:
        root_path: The root directory to start scanning. Defaults to the current
            working directory.
        registry: The registry instance to register definitions into. Defaults to
            the global registry.
        walker_func: A callable that behaves like os.walk. Defaults to `_default_walker`.
        file_reader: A callable that reads a file path and returns content.
            Defaults to `_default_file_reader`.
    """
    if root_path is None:
        root_path = os.getcwd()
    if registry is None:
        registry = get_registry()
    if walker_func is None:
        walker_func = _default_walker
    if file_reader is None:
        file_reader = _default_file_reader

    logger.debug(f"Scanning for PromptFlow DAGs in {root_path}...")

    dag_files = []
    # Use the injected walker
    for root, dirs, files in walker_func(root_path):
        if "flow.dag.yaml" in files:
            dag_files.append(os.path.join(root, "flow.dag.yaml"))

    count = 0
    for dag_path in dag_files:
        try:
            _process_dag_file(dag_path, registry, file_reader)
            count += 1
        except Exception as e:
            logger.warning(f"Error parsing DAG {dag_path}: {e}", exc_info=True)

    if count > 0:
        logger.debug(f"Processed {count} PromptFlow DAGs.")


def _process_dag_file(dag_path: str, registry: AgentRegistry, file_reader: Callable):
    """Parses a single PromptFlow DAG file and registers its templates.

    Args:
        dag_path: The path to the `flow.dag.yaml` file.
        registry: The registry instance to use.
        file_reader: The callable used to read files.
    """
    base_dir = os.path.dirname(dag_path)

    # YAML reading via injected reader
    try:
        content = file_reader(dag_path)
        data = yaml.safe_load(content) or {}
    except Exception as e:
        logger.warning(e, exc_info=True)
        return

    nodes = data.get("nodes", [])
    for node in nodes:
        node_type = node.get("type")
        if node_type in ("prompt", "llm"):
            source_file = (
                node.get("source", {}).get("path")
                if isinstance(node.get("source"), dict)
                else node.get("source")
            )

            if (
                source_file
                and isinstance(source_file, str)
                and (source_file.endswith(".jinja2") or source_file.endswith(".j2"))
            ):
                # NOTE: here we build absolute paths; if using a mock walker ensure paths are consistent
                abs_jinja_path = os.path.abspath(os.path.join(base_dir, source_file))

                # Here we perform a "lazy" existence check: try to read it with the reader.
                # If the reader fails, assume the file does not exist.
                _register_jinja_file(
                    abs_jinja_path,
                    node.get("name", "unknown_node"),
                    registry,
                    file_reader,
                )


def _register_jinja_file(
    filepath: str, node_name: str, registry: AgentRegistry, file_reader: Callable
):
    """Registers a specific Jinja2 file content into the registry.

    Args:
        filepath: The absolute path to the Jinja2 file.
        node_name: The name of the node in the PromptFlow DAG.
        registry: The registry instance.
        file_reader: The callable used to read the file.
    """
    try:
        content = file_reader(filepath)

        # Unique ID based on file path
        canonical_id = f"FILE:{filepath}"

        # Map content hash -> File ID
        registry.register_content_map(content, canonical_id)

        preview = content.strip().replace("\n", " ")[:50]

        registry.register_definition(
            key=canonical_id,
            kind="PROMPT",
            metadata={
                "class": "PromptFlow::Jinja2",
                "preview": preview,
                "tool_name": node_name,
                "file_path": filepath,
                "line_number": 1,
            },
        )
        logger.debug(f"Registered PromptFlow template: {filepath}")

    except Exception as e:
        logger.warning(f"Error reading jinja {filepath}: {e}", exc_info=True)
