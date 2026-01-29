"""Raw string heuristic scanner.

Not all prompts use `PromptTemplate` classes. Many developers use simple global
string variables or f-strings. This module scans your codebase for string
variables that match specific naming conventions.

Heuristics:
    By default, it looks for variables starting with prefixes like `PROMPT_`
    or ending with suffixes like `_TEMPLATE`.

    It handles **f-strings** by creating a robust regex that matches the variable
    content, replacing `{variables}` with wildcard patterns (`.*?`).

Examples:
    If your code has:
    ```python
    # my_agent.py
    SALES_PROMPT = "Hello {user}, buy this!"
    ```
    This scanner detects `SALES_PROMPT` and creates a coverage target that matches
    any runtime string starting with "Hello " and ending with ", buy this!".
"""

import logging
import os
import re
import sys
from typing import Any, Callable, Dict, List, Optional

from agent_cover.registry import AgentRegistry, get_registry

logger = logging.getLogger(__name__)


DEFAULT_PREFIXES = ["PROMPT_", "TEMPLATE_", "SYS_MSG_", "SYSTEM_MESSAGE"]
"""Default prefixes used to identify potential prompt variables."""
DEFAULT_SUFFIXES = ["_PROMPT", "_TEMPLATE"]
"""Default suffixes used to identify potential prompt variables."""
_custom_prefixes = []
"""List to hold custom prefixes for prompt variable identification."""
_custom_suffixes = []
"""List to hold custom suffixes for prompt variable identification."""


def set_custom_prefixes(prefixes: list[str]) -> None:
    """Sets custom prefixes for identifying prompt variables.

    Args:
        prefixes: A list of string prefixes.
    """
    global _custom_prefixes
    _custom_prefixes = [p.strip() for p in prefixes if p.strip()]


def set_custom_suffixes(suffixes: list[str]) -> None:
    """Sets custom suffixes for identifying prompt variables.

    Args:
        suffixes: A list of string suffixes.
    """
    global _custom_suffixes
    _custom_suffixes = [s.strip() for s in suffixes if s.strip()]


def _create_robust_regex(text: str) -> str:
    """Creates a robust regular expression from a given text.

    This function preprocesses the input text to create a regular
    expression that can handle variations in whitespace and variable
    placeholders (e.g., {variable_name}).

    Args:
        text: The input string to convert to a regex.

    Returns:
        A string representing the robust regular expression.
    """
    # 1. Normalize whitespace first: turn all newlines/tabs into single spaces
    clean_text = " ".join(text.split())
    if not clean_text:
        return ""

    # 2. Escape the normalized string
    escaped_text = re.escape(clean_text)

    # 3. Restore F-String variables ({var} -> .*?)
    # Note: re.escape might escape '{' to '\{' depending on python version
    escaped_text = re.sub(r"\\\{[a-zA-Z0-9_]+\\\}", r".*?", escaped_text)

    # 4. Allow flexible whitespace in the regex (\s+)
    # Replace literal spaces with \s+ to match newlines/tabs at runtime
    escaped_text = escaped_text.replace(r"\ ", r"\s+")

    return escaped_text


# --- DEFAULT HELPERS ---
def _default_module_iterator() -> Dict[str, Any]:
    """Provides a default module iterator.

    Returns:
        A dictionary where keys are module names and values are the
        corresponding modules.
    """
    return dict(sys.modules)


def _default_source_reader(filepath: str) -> List[str]:
    """Reads the source file and returns its lines.

    Args:
        filepath: The path to the source file.

    Returns:
        A list of strings, where each string is a line from the file.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.readlines()
    except Exception as e:
        logger.warning(e, exc_info=True)
        return []


def _find_variable_line_number(var_name: str, lines: List[str]) -> int:
    """Finds the line number of a variable definition.

    Args:
        var_name: The name of the variable to find.
        lines: A list of strings, where each string is a line of code.

    Returns:
        The line number of the variable definition, or 0 if not found.
    """
    pattern = re.compile(rf"^\s*{var_name}\s*=")
    for i, line in enumerate(lines):
        if pattern.match(line):
            return i + 1
    return 0


def scan_raw_string_prompts(
    registry: Optional[AgentRegistry] = None,
    root_path: Optional[str] = None,
    module_iterator: Optional[Callable[[], Dict[str, Any]]] = None,
    source_reader: Optional[Callable[[str], List[str]]] = None,
) -> None:
    """Scans for raw string prompts in Python modules and registers them.

    It iterates through all loaded modules in `sys.modules` that reside within
    `root_path`. For each string variable matching the configured prefixes/suffixes,
    it:
    1.  Calculates a regex pattern for runtime matching.
    2.  Registers it in the [`AgentRegistry`][agent_cover.registry.AgentRegistry].

    Args:
        registry: An optional AgentRegistry instance. If not provided, it
            defaults to the global registry.
        root_path: An optional root path to start the scan from. If not
            provided, it defaults to the current working directory.
        module_iterator: An optional callable for iterating through
            loaded modules.  Defaults to _default_module_iterator.
        source_reader: An optional callable for reading source file
            contents.  Defaults to _default_source_reader.
    """
    if registry is None:
        registry = get_registry()
    if root_path is None:
        root_path = os.getcwd()  # Default Prod
    if module_iterator is None:
        module_iterator = _default_module_iterator
    if source_reader is None:
        source_reader = _default_source_reader

    active_prefixes = tuple(DEFAULT_PREFIXES + _custom_prefixes)
    active_suffixes = tuple(DEFAULT_SUFFIXES + _custom_suffixes)

    modules_snapshot = module_iterator()

    for mod_name, mod in modules_snapshot.items():
        if not hasattr(mod, "__file__") or not mod.__file__:
            continue
        mod_file = os.path.abspath(mod.__file__)

        if not mod_file.startswith(root_path) or "site-packages" in mod_file:
            continue

        file_lines = None

        for name, val in list(vars(mod).items()):
            if not isinstance(val, str):
                continue

            match_prefix = name.startswith(active_prefixes)
            match_suffix = name.endswith(active_suffixes)

            if not (match_prefix or match_suffix):
                continue

            if len(val) < 10:
                continue

            if file_lines is None:
                file_lines = source_reader(mod_file)

            line_num = _find_variable_line_number(name, file_lines)
            if line_num == 0:
                continue

            clean_content = val.strip()
            regex_pattern = _create_robust_regex(clean_content)

            raw_id = f"RAW:{mod_file}::{name}"
            canonical_id = registry.get_canonical_id(clean_content, raw_id)

            if canonical_id not in registry.definitions:
                logger.debug(
                    f"[AgentCover][SCAN] Found {name} at line {line_num} in {mod_file}"
                )
                registry.register_definition(
                    key=canonical_id,
                    kind="PROMPT",
                    metadata={
                        "class": "StringConstant",
                        "preview": clean_content[:40],
                        "raw_content": clean_content,
                        "regex_pattern": regex_pattern,
                        "line_number": line_num,
                    },
                )
