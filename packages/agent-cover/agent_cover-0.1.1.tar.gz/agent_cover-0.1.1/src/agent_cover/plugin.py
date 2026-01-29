"""Pytest plugin for Agent Coverage integration.

This module implements the pytest hooks necessary to integrate Agent Coverage
into the test execution flow. It orchestrates the entire lifecycle:
1.  **Setup**: Parses CLI options (`--agent-cov`, etc.).
2.  **Instrumentation**: Initializes the [`AgentCoverage`][agent_cover.manager.AgentCoverage] manager before tests start.
3.  **Teardown**: Generates reports (JSON/XML/HTML) after tests finish.

## CLI Options

The plugin adds the following flags to the `pytest` command line:

| Option | Description | Default |
| :--- | :--- | :--- |
| `--agent-cov` | Enable the plugin. Must be present to run instrumentation. | `False` |
| `--agent-cov-html=<dir>` | Directory to generate the static HTML report. | `None` |
| `--agent-cov-xml=<file>` | Path to generate the Cobertura XML report (CI/CD). | `None` |
| `--agent-cov-json=<file>` | Path to generate the raw JSON data dump. | `agent_coverage.json` |
| `--agent-source-dir=<dir>` | Root directory to scan for python modules (Discovery phase). | Current Working Dir |
| `--prompt-prefixes=<list>` | Comma-separated list of variable prefixes to scan as Raw Strings. | `None` |
| `--prompt-suffixes=<list>` | Comma-separated list of variable suffixes to scan as Raw Strings. | `None` |
| `--agent-cov-verbose` | Enable debug logging specifically for AgentCover internals. | `False` |

Hooks Implemented:
    - `pytest_addoption`: Registers custom CLI flags.
    - `pytest_configure`: Starts instrumentation and scans for static definitions.
    - `pytest_sessionfinish`: Generates reports using data collected during the run.
    - `pytest_unconfigure`: Clean up and stop instrumentation.
"""

import json
import logging
import os
import shutil
import sys

import pytest

from agent_cover.config import load_config
from agent_cover.discovery import discover_repository_modules
from agent_cover.instrumentation import scan_static_definitions
from agent_cover.instrumentation.promptflow import scan_promptflow_definitions
from agent_cover.instrumentation.raw_strings.scanner import (
    set_custom_prefixes,
    set_custom_suffixes,
)

# --- LOCAL MODULE IMPORTS ---
from agent_cover.manager import AgentCoverage
from agent_cover.reporting.html import generate_html_report

# Reporting
from agent_cover.reporting.xml import generate_cobertura_xml
from agent_cover.utils import format_iso_time, get_timestamp

logger = logging.getLogger(__name__)

# --- STASH KEYS ---
MANAGER_KEY = pytest.StashKey()


# 1. CLI Option Definitions
def pytest_addoption(parser):
    """Registers the command-line options for agent coverage.

    These options allow users to enable coverage, specify report paths, and
    customize heuristic scanning without changing code.

    Args:
        parser: The pytest parser object.
    """
    group = parser.getgroup("agent-cover", "Agent Coverage Reporting")

    group.addoption(
        "--agent-cov",
        action="store_true",
        default=False,
        help="Enable Agent Coverage reporting.",
    )
    group.addoption(
        "--agent-cov-json",
        action="store",
        default="agent_coverage.json",
        help="Path to save the JSON report.",
    )
    group.addoption(
        "--agent-cov-xml",
        action="store",
        default=None,
        help="Path to save the Cobertura XML report.",
    )
    group.addoption(
        "--agent-cov-html",
        action="store",
        default=None,
        help="Directory where to save the HTML report.",
    )
    group.addoption(
        "--agent-source-dir",
        action="store",
        default=None,
        help="Directory to scan for python modules (discovery).",
    )
    group.addoption(
        "--prompt-prefixes",
        action="store",
        default=None,
        help="Comma-separated list of variable prefixes to treat as prompts (e.g. 'MY_PROMPT_,TEXT_').",
    )
    group.addoption(
        "--prompt-suffixes",
        action="store",
        default=None,
        help="Comma-separated list of variable suffixes (e.g. '_PROMPT,_TEXT').",
    )

    group.addoption(
        "--agent-cov-verbose",
        action="store_true",
        default=False,
        help="Enable debug logging specifically for AgentCover.",
    )


# 2. Configuration and Startup Hook
def pytest_configure(config):
    """Initializes the AgentCoverage manager, loads the config, and applies patches.

    This hook runs **before** any test is executed. It is responsible for:
    1.  Loading `agent-cover.yaml`.
    2.  Starting the [Instrumentation][agent_cover.manager.AgentCoverage.start].
    3.  Performing an initial static scan of the codebase to find Prompts and Tools.

    Args:
        config: The pytest configuration object.
    """
    # VERBOSE MANAGEMENT
    if config.getoption("--agent-cov-verbose"):
        if config.option.capture != "no":
            config.option.capture = "no"

        # Configure your package's ROOT logger
        pkg_logger = logging.getLogger("agent_cover")
        pkg_logger.setLevel(logging.DEBUG)

        # Detach the logger from the parent hierarchy.
        # This prevents Pytest or Promptflow from blocking your DEBUG logs.
        pkg_logger.propagate = False

        # Clean up old/inherited handlers
        if pkg_logger.hasHandlers():
            pkg_logger.handlers.clear()

        # Create a new handler on STDOUT (safe with -s flag)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter("[\033[96mAgentCover\033[0m] %(message)s")
        handler.setFormatter(formatter)

        pkg_logger.addHandler(handler)

        pkg_logger.debug("Logger configured and handler attached successfully.")

    if not config.getoption("--agent-cov"):
        return

    logger.debug("Plugin enabled via CLI.")

    # --- 1. Environment Setup and Configuration ---
    source_dir = config.getoption("--agent-source-dir") or os.getcwd()
    abs_source = os.path.abspath(source_dir)

    if abs_source not in sys.path:
        sys.path.insert(0, abs_source)

    # Load YAML configuration
    agent_config = load_config(abs_source)

    # Prefixes/Suffixes Configuration (Raw Strings)
    prefixes_str = config.getoption("--prompt-prefixes")
    if prefixes_str:
        set_custom_prefixes(prefixes_str.split(","))

    suffixes_str = config.getoption("--prompt-suffixes")
    if suffixes_str:
        set_custom_suffixes(suffixes_str.split(","))

    # --- 2. Start Manager ---
    cov_manager = AgentCoverage(config=agent_config)

    try:
        cov_manager.start()

        # Save the manager in the stash for later retrieval
        config.stash[MANAGER_KEY] = cov_manager

        logger.debug("Instrumentation applied via Manager.")
    except Exception as e:
        logger.critical(f"Critical Error starting instrumentation: {e}", exc_info=True)

    # --- 3. Initial Static Scan (PromptFlow) ---
    try:
        scan_promptflow_definitions(root_path=abs_source, registry=cov_manager.registry)
    except Exception as e:
        logger.warning(f"PromptFlow scan warning: {e}", exc_info=True)


def pytest_sessionfinish(session, exitstatus):
    """Generates reports at the end of the session.

    This hook runs **after** all tests have completed. It:
    1.  Runs a final discovery sweep (to catch dynamically defined objects).
    2.  Extracts execution data from the [`AgentRegistry`][agent_cover.registry.AgentRegistry].
    3.  Calls the reporting modules to generate JSON, XML, and HTML files.

    Args:
        session: The pytest session object.
        exitstatus: The exit status of the test run.
    """
    manager = session.config.stash.get(MANAGER_KEY, None)
    if not manager:
        return

    source_dir = session.config.getoption("--agent-source-dir") or os.getcwd()

    # --- 1. Final Discovery and Static Scan ---
    try:
        logger.debug("Running final discovery...")
        discover_repository_modules(root_path=os.path.abspath(source_dir))

        scan_static_definitions(registry=manager.registry, config=manager.config)
    except Exception as e:
        logger.warning(f"Final discovery warning: {e}", exc_info=True)

    # --- 2. Data Extraction ---
    registry = manager.registry
    config_obj = manager.config

    definitions = registry.definitions
    executions = registry.executions
    decision_hits = registry.decision_hits

    # --- 3. Common Timestamp Setup ---
    # Generate a single timestamp for consistency across all reports
    common_timestamp = get_timestamp()

    # --- 4. JSON Report Generation ---
    json_path = session.config.getoption("--agent-cov-json")
    _save_json_report(
        definitions,
        executions,
        config_obj,
        decision_hits,
        json_path,
        timestamp=common_timestamp,
    )

    # --- 5. XML Report Generation ---
    xml_path = session.config.getoption("--agent-cov-xml")
    if xml_path:
        generate_cobertura_xml(
            definitions,
            executions,
            config_obj,
            decision_hits,
            xml_path,
            timestamp=common_timestamp,
        )
        logger.debug(f"XML Report generated: {xml_path}")

    # --- 6. HTML Report Generation ---
    html_dir = session.config.getoption("--agent-cov-html")
    if html_dir:
        report_path = generate_html_report(
            definitions,
            executions,
            html_dir,
            decision_config=config_obj,
            decision_hits=decision_hits,
            timestamp=common_timestamp,
        )
        logger.debug(f"HTML Report generated: {report_path}/index.html")


def pytest_unconfigure(config):
    """Cleans up resources when the pytest session ends.

    Args:
        config: The pytest configuration object.
    """
    manager = config.stash.get(MANAGER_KEY, None)
    if manager:
        logger.debug("Stopping instrumentation (Cleanup)...")
        manager.stop()


# --- TERMINAL REPORTING ---


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Outputs a coverage summary to the terminal.

    Args:
        terminalreporter: The pytest terminal reporter object.
        exitstatus: The exit status of the test run.
        config: The pytest configuration object.
    """
    manager = config.stash.get(MANAGER_KEY, None)
    if not manager:
        return

    registry = manager.registry
    agent_config = manager.config

    if not registry.definitions and (not agent_config or not agent_config.decisions):
        return

    definitions = registry.definitions
    executions = registry.executions
    decision_hits = registry.decision_hits

    prompts = {
        k: v
        for k, v in definitions.items()
        if v.get("kind") == "PROMPT" or v.get("type") == "PROMPT"
    }

    tools = {
        k: v
        for k, v in definitions.items()
        if v.get("kind") == "TOOL" or v.get("type") == "TOOL"
    }

    if prompts:
        _print_coverage_table(
            terminalreporter, "Prompt Coverage", prompts, executions, color="purple"
        )

    if tools or (agent_config and agent_config.decisions):
        _print_coverage_table(
            terminalreporter,
            "Completion Coverage",
            tools,
            executions,
            extra_decisions=agent_config,
            decision_hits=decision_hits,
            color="yellow",
        )


# --- HELPER FUNCTIONS ---


def _save_json_report(defs, execs, config, dec_hits, path, timestamp=None):
    """Saves a complete JSON report.

    Uses `format_iso_time` to ensure testability (avoiding direct datetime.now()).

    Args:
        defs: Dictionary of definitions.
        execs: Set of executed definition IDs.
        config: The agent configuration object.
        dec_hits: Dictionary of decision hits.
        path: File path to save the JSON.
        timestamp: Optional timestamp string.
    """
    prompts_data = {}
    tools_data = {}

    for k, v in defs.items():
        is_hit = k in execs
        item = {**v, "executed": is_hit}

        if v.get("kind") == "PROMPT":
            prompts_data[k] = item
        elif v.get("kind") == "TOOL":
            tools_data[k] = item

    decisions_data = []
    if config and config.decisions:
        for dec in config.decisions:
            hits = dec_hits.get(dec.id, [])
            hits_list = list(hits) if isinstance(hits, set) else list(hits)

            expected = set(dec.expected_values)
            observed = set(hits)
            missed_values = list(expected - observed)

            decisions_data.append(
                {
                    "id": dec.id,
                    "description": dec.description,
                    "target_field": dec.target_field,
                    "expected_values": dec.expected_values,
                    "observed_values": hits_list,
                    "missed_values": missed_values,
                    "coverage_percent": (len(observed) / len(expected) * 100)
                    if expected
                    else 0,
                }
            )

    report = {
        "timestamp": format_iso_time(timestamp),  # Uses testable helper
        "summary": {
            "prompts_total": len(prompts_data),
            "prompts_executed": sum(1 for p in prompts_data.values() if p["executed"]),
            "tools_total": len(tools_data),
            "tools_executed": sum(1 for t in tools_data.values() if t["executed"]),
            "decisions_defined": len(decisions_data),
        },
        "prompts": prompts_data,
        "tools": tools_data,
        "business_decisions": decisions_data,
    }

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
    except Exception as e:
        logger.warning(f"Error saving JSON: {e}", exc_info=True)


def _print_coverage_table(
    terminalreporter,
    title,
    definitions,
    executions,
    extra_decisions=None,
    decision_hits=None,
    color="white",
):
    """Prints a formatted coverage table to the terminal.

    Args:
        terminalreporter: The pytest terminal reporter object.
        title: The title of the table section.
        definitions: Dictionary of code definitions.
        executions: Set of executed IDs.
        extra_decisions: Optional configuration object containing business decisions.
        decision_hits: Optional dictionary tracking hits for business decisions.
        color: The color of the terminal section.
    """
    # 1. Calculate the terminal width
    # fallback=(120, 24) is useful if the command is run in a non-interactive environment (e.g., CI/CD)
    terminal_width = shutil.get_terminal_size(fallback=(120, 24)).columns

    # 2. Set a minimum width to prevent table columns from breaking.
    # (Your columns add up to about 115-120 characters, so 120 is a good minimum.)
    sep_width = max(terminal_width, 120)

    style_kwargs = {color: True, "bold": True}

    terminalreporter.section(title, sep="=", **style_kwargs)

    # --- 1. Business Logic ---
    if extra_decisions and extra_decisions.decisions:
        terminalreporter.write("Business Logic (Configured & Structures)\n", bold=True)
        terminalreporter.write("-" * sep_width + "\n")

        header = f"{'Decision ID':<30} {'Field':<15} {'Missed Values':<25} {'Cover':>7} {'File':<25} {'Line':<6}\n"
        terminalreporter.write(header)
        terminalreporter.write("-" * sep_width + "\n")

        for dec in extra_decisions.decisions:
            hits = decision_hits.get(dec.id, set()) if decision_hits else set()
            expected = set(dec.expected_values)
            missed = expected - hits
            pct = (len(hits) / len(expected) * 100) if expected else 0

            missed_str = ", ".join(list(missed)[:3])
            if len(missed) > 3:
                missed_str += "..."
            if not missed:
                missed_str = ""

            col = {"green": True} if pct == 100 else {"red": True}

            fpath = dec.file_path or ""
            try:
                rel_path = os.path.relpath(fpath, os.getcwd())
            except ValueError:
                rel_path = fpath

            if len(rel_path) > 24:
                rel_path = "..." + rel_path[-21:]

            line_str = str(dec.line_number) if dec.line_number > 0 else "-"

            row = f"{dec.id:<30} {dec.target_field:<15} {missed_str:<25} {pct:>6.0f}% {rel_path:<25} {line_str:<6}\n"
            terminalreporter.write(row, **col)
        terminalreporter.write("\n")

    # --- 2. Code Objects (File Based) ---
    if definitions:
        if extra_decisions:
            terminalreporter.write("Internal Tools (Code)\n", bold=True)

        header = f"{'File':<42} {'Item':>5} {'Miss':>5} {'Cover':>7} {'Variable/Tool':<25} {'Lines':>8} {'Preview':<25}\n"
        terminalreporter.write("-" * sep_width + "\n")
        terminalreporter.write(header, bold=True)
        terminalreporter.write("-" * sep_width + "\n")

        from collections import defaultdict

        files = defaultdict(list)
        for key, meta in definitions.items():
            if key.startswith("RAW:"):
                clean_key = key[4:]
                fpath = clean_key.split("::")[0]
            elif key.startswith("FILE:"):
                fpath = key[5:]
            else:
                fpath = key.split(":")[0]
            files[fpath].append((key, meta))

        sorted_files = sorted(files.keys())
        total_items = 0
        total_missed = 0

        for fpath in sorted_files:
            items = files[fpath]
            try:
                rel_path = os.path.relpath(fpath, os.getcwd())
            except ValueError:
                rel_path = fpath

            if len(rel_path) > 41:
                rel_path = "..." + rel_path[-38:]

            n_items = len(items)
            missed_pairs = []
            preview_rows = []

            for key, meta in items:
                is_missed = key not in executions
                if is_missed:
                    missed_pairs.append((key, meta))

                line_str = "?"
                if "line_number" in meta and meta["line_number"] > 0:
                    line_str = str(meta["line_number"])
                elif not key.startswith("RAW:"):
                    try:
                        line_str = key.split(":")[1].split("#")[0]
                    except IndexError:
                        pass

                var_name = ""
                if key.startswith("RAW:"):
                    var_name = key.split("::")[-1]
                elif "tool_name" in meta:
                    var_name = meta["tool_name"]
                elif "class" in meta:
                    var_name = f"<{meta['class']}>"
                if len(var_name) > 23:
                    var_name = var_name[:21] + ".."

                raw_preview = (meta.get("preview") or "").replace("\n", " ")
                if var_name and raw_preview.startswith(var_name):
                    parts = raw_preview.split(":", 1)
                    if len(parts) > 1:
                        raw_preview = parts[1].strip()
                if len(raw_preview) > 60:
                    raw_preview = raw_preview[:60] + "..."

                row_str = f"{var_name:<25} {line_str:>8} {raw_preview}"
                item_color = {"red": True} if is_missed else {"green": True}
                preview_rows.append((row_str, item_color))

            n_missed = len(missed_pairs)
            pct = ((n_items - n_missed) / n_items) * 100 if n_items > 0 else 0
            file_color = {"green": True} if n_missed == 0 else {"red": True}

            terminalreporter.write(
                f"{rel_path:<42} {n_items:>5} {n_missed:>5} {pct:>6.0f}% {'':<25} {'':>8} ",
                **file_color,
            )
            terminalreporter.write("\n")

            padding = " " * 63
            for txt, col in preview_rows:
                terminalreporter.write(f"{padding}{txt}\n", **col)

            total_items += n_items
            total_missed += n_missed

        terminalreporter.write("-" * sep_width + "\n")

        total_pct = (
            ((total_items - total_missed) / total_items) * 100 if total_items > 0 else 0
        )
        color_total = {"green": True} if total_pct > 80 else {"red": True}

        terminalreporter.write(
            f"{'TOTAL CODE OBJECTS':<42} {total_items:>5} {total_missed:>5} {total_pct:>6.0f}%\n",
            **color_total,
        )
        terminalreporter.write("\n")
