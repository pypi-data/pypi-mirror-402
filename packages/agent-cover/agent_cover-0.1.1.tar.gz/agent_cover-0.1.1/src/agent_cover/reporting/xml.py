"""Cobertura XML Generator for CI/CD Integration.

This module converts AgentCover's rich data into the standard Cobertura XML format.
This allows tools like **GitLab CI**, **Jenkins**, or **Codecov** to visualize
agent coverage alongside standard code coverage.

Mapping Logic:
    - **Source Code**: Prompts and Tools are mapped to their actual file and line number.
    - **Virtual Decisions**: Business rules (e.g., "Expected Intents") are mapped to
      a virtual file named `agent-cover.yaml`. Each expected value counts as a "line"
      to be covered.
"""

import logging
import os
import xml.etree.ElementTree as ET
from typing import Any, Callable, Dict, List, Optional, Set

from agent_cover.utils import get_timestamp

logger = logging.getLogger(__name__)


def _default_file_writer(path: str, content: str) -> None:
    """Writes content to a file, creating the directory structure if needed.

    This is the default I/O handler used if no custom writer function is provided.

    Args:
        path: The absolute or relative file path where the content should be saved.
        content: The string content to write to the file.
    """
    dirname = os.path.dirname(path)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def generate_cobertura_xml(
    definitions: Dict[str, Any],
    executions: Any,
    config: Optional[Any] = None,
    decision_hits: Optional[Dict[str, Set[str]]] = None,
    output_file: str = "coverage.xml",
    writer_func: Optional[Callable[[str, str], None]] = None,
    timestamp: Optional[float] = None,
) -> None:
    """Generates a Cobertura XML coverage report.

    This function calculates coverage statistics for both actual source code lines
    and virtual decision lines (from YAML configuration). It constructs an XML
    tree following the Cobertura DTD and writes it to disk.

    Args:
        definitions: A dictionary containing the definitions of code items
            (e.g., lines, statements) to be tracked.
        executions: A collection (set or dict) of definition keys that were
            actually executed during the run.
        config: An optional configuration object containing `decisions`.
            If provided, coverage for these decisions is added to the report.
        decision_hits: An optional dictionary mapping decision IDs to sets of
            observed values. Used to calculate 'virtual' coverage.
        output_file: The file path for the output XML report. Defaults to
            "coverage.xml".
        writer_func: An optional callable to handle the file writing process.
            If None, the default disk writer is used. Useful for testing or
            writing to non-disk buffers.
        timestamp: An optional Unix timestamp (float) to force a specific time
            in the report header. If None, the current system time is used.
    """
    # Use default file writer if none is provided
    if writer_func is None:
        writer_func = _default_file_writer

    decision_hits = decision_hits or {}

    # Determine timestamp (Timestamp injection)
    ts = timestamp if timestamp is not None else get_timestamp()

    root = ET.Element("coverage")
    root.set("version", "1.0")
    root.set("timestamp", str(int(ts)))

    file_items = {k: v for k, v in definitions.items()}
    total_lines = len(file_items)
    covered_lines = sum(1 for k in file_items if k in executions)

    yaml_lines = 0
    yaml_covered = 0
    if config and config.decisions:
        for dec in config.decisions:
            yaml_lines += len(dec.expected_values)
            hits = decision_hits.get(dec.id, set())
            yaml_covered += sum(1 for v in dec.expected_values if str(v) in hits)

    grand_total = total_lines + yaml_lines
    grand_covered = covered_lines + yaml_covered

    line_rate = grand_covered / grand_total if grand_total > 0 else 0
    root.set("line-rate", f"{line_rate:.4f}")
    root.set("lines-covered", str(grand_covered))
    root.set("lines-valid", str(grand_total))

    packages = ET.SubElement(root, "packages")

    # Package 1: Source Code
    files_data: Dict[str, List[Dict[str, Any]]] = {}
    for key, meta in file_items.items():
        # --- ID Parsing Logic ---
        if key.startswith("RAW:"):
            # Format: RAW:/path/to/file.py::VAR_NAME
            fpath = key[4:].split("::")[0]
        elif key.startswith("FILE:"):
            # Format: FILE:/path/to/template.jinja2
            fpath = key[5:]
        else:
            # Format: /path/to/file.py:123 or /path/to/file.py:TOOL:name
            fpath = key.split(":")[0]

        if fpath not in files_data:
            files_data[fpath] = []

        # --- Line Number Extraction ---
        # Priority 1: Metadata (Reliable, set by scanners)
        lineno = meta.get("line_number", 0)

        # Priority 2: ID Parsing (Legacy fallback for old standard IDs)
        if lineno == 0 and not key.startswith("RAW:") and not key.startswith("FILE:"):
            try:
                parts = key.split(":")
                if len(parts) >= 2:
                    # Check if second part is a line number (path:123)
                    candidate = parts[1].split("#")[0]
                    if candidate.isdigit():
                        lineno = int(candidate)
            except (IndexError, ValueError):
                pass

        files_data[fpath].append({"line": lineno, "hit": key in executions})

    src_pkg = ET.SubElement(packages, "package")
    src_pkg.set("name", "source_code")
    src_classes = ET.SubElement(src_pkg, "classes")

    for fpath, lines in files_data.items():
        try:
            rel_path = os.path.relpath(fpath, os.getcwd())
        except ValueError:
            # Handles cases where paths are on different drives (Windows)
            rel_path = fpath

        cls = ET.SubElement(src_classes, "class")
        cls.set("name", rel_path)
        cls.set("filename", rel_path)

        xml_lines = ET.SubElement(cls, "lines")
        for item in lines:
            le = ET.SubElement(xml_lines, "line")
            le.set("number", str(item["line"]))
            le.set("hits", "1" if item["hit"] else "0")

    # Package 2: Virtual Decisions
    if config and config.decisions:
        dec_pkg = ET.SubElement(packages, "package")
        dec_pkg.set("name", "decisions")
        dec_classes = ET.SubElement(dec_pkg, "classes")

        cls = ET.SubElement(dec_classes, "class")
        cls.set("name", "agent-cover.yaml")
        cls.set("filename", "agent-cover.yaml")
        xml_lines = ET.SubElement(cls, "lines")

        virtual_line_cnt = 1
        for dec in config.decisions:
            hits = decision_hits.get(dec.id, set())
            for val in dec.expected_values:
                is_hit = str(val) in hits
                le = ET.SubElement(xml_lines, "line")
                le.set("number", str(virtual_line_cnt))
                le.set("hits", "1" if is_hit else "0")
                virtual_line_cnt += 1

    try:
        # Indent XML if supported (Python 3.9+)
        if hasattr(ET, "indent"):
            ET.indent(root, space="  ", level=0)

        xml_str = ET.tostring(root, encoding="utf-8", method="xml").decode("utf-8")

        if not xml_str.startswith("<?xml"):
            xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str

        writer_func(output_file, xml_str)

    except Exception as e:
        logger.warning(f"XML Error: {e}", exc_info=True)
