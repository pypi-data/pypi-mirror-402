"""CLI entry point for the AgentCover orchestration utility.

This module provides the primary command-line interface for AgentCover,
specifically the `run` command. It is designed to solve the challenge of
instrumenting LLM agents in multi-process or distributed environments
(e.g., Microsoft PromptFlow batch runs).

The orchestration follows a specialized "Injection & Aggregation" lifecycle:

1.  **Bootstrapping**: The CLI creates a temporary directory containing a
    `sitecustomize.py` script. This script is injected into the `PYTHONPATH`
    of the target command. Because Python executes `sitecustomize` on startup,
    every child process spawned by the command is automatically instrumented
    without requiring code changes.
2.  **Distributed Collection**: As worker processes run (even in parallel),
    they record hits for prompts and tools, saving local coverage data as
    `fragment_PID.json` files in the report directory.
3.  **Consolidation**: Once the main command finishes, the CLI "hydrates"
     the registry by scanning the local source code and merges all worker
     fragments into a single, unified HTML/XML report.

Examples:
    Instrumenting a Microsoft PromptFlow batch execution:

    ```bash
    $ agent-cover run --source-dir ./src -- pf run create --flow ./my_flow --data ./data.jsonl
    ```

    Instrumenting a standard Python script to ensure aggregation:

    ```bash
    $ agent-cover run --report-dir ./custom_logs -- python agent_main.py
    ```

    Using the double-dash separator to pass complex arguments:
    ```bash
    $ agent-cover run --source-dir . -- pytest -v ./tests/test_agents.py
    ```

Attributes:
    AC_PREFIX (str): The ANSI-formatted prefix used for AgentCover CLI logging.
    BOOTSTRAP_TEMPLATE (str): The Python template used to generate the
        injection script for child processes.
"""

import argparse
import glob
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile

# --- ANSI Color Codes ---
CYAN = "\033[96m"
RESET = "\033[0m"
# Formatted prefix: [AgentCover] with the name in cyan
AC_PREFIX = f"[{CYAN}AgentCover{RESET}]"

# Bootstrap script template injected into every child process.
# It ensures that 'sitecustomize.py' is executed by the Python interpreter
# upon startup, regardless of how the process was spawned.
BOOTSTRAP_TEMPLATE = """
import os
import sys

# ANSI codes inside the bootstrap string
CYAN = "\\033[96m"
RESET = "\\033[0m"
PREFIX = f"[{{CYAN}}AgentCover{{RESET}}]"

source_path = "{source_dir}"
if source_path not in sys.path:
    sys.path.insert(0, source_path)

os.environ["AGENT_COVER_BOOTSTRAPPED"] = "1"

try:
    import agent_cover.sdk
    # Notifica di caricamento del worker
    sys.__stderr__.write(f"{{PREFIX}} Worker {{os.getpid()}} initialized.\\n")

    agent_cover.sdk.start_coverage(
        report_dir="{report_dir}",
        source_dir="{source_dir}",
        auto_save=True
    )
except Exception as e:
    sys.__stderr__.write(f"{{PREFIX}} Bootstrap Error: {{e}}\\n")
"""

logger = logging.getLogger(__name__)


def aggregate_and_report(report_dir: str, source_dir: str) -> None:
    """Consolidates distributed coverage fragments into a final report.

    This function is executed by the parent process after the target command
    finishes. It performs 'Hydration' of the registry (static discovery of
    all available prompts/tools) and then merges the runtime hits collected
    by distributed worker processes.

    Args:
        report_dir: Directory where workers saved their JSON fragments.
        source_dir: Root directory of the source code for static scanning.

    Note:
        Fragments are deleted after a successful merge to ensure the
        report directory stays clean for subsequent runs.
    """
    from agent_cover.config import load_config
    from agent_cover.instrumentation import instrument_all, scan_static_definitions
    from agent_cover.registry import registry
    from agent_cover.sdk import generate_report

    print(f"{AC_PREFIX} Aggregating worker results from {report_dir}...")

    # 1. Hydrate the Parent Registry
    # We must load definitions so the aggregator knows the 'total' coverage targets.
    try:
        load_config(source_dir)
        instrument_all()  # Pre-loads targets defined in modules
        scan_static_definitions(root_path=source_dir)
    except Exception as e:
        print(f"{AC_PREFIX} Error during static discovery: {e}")

    # 2. Merge JSON fragments
    # Workers save their state into individual 'fragment_PID.json' files.
    fragments = glob.glob(os.path.join(report_dir, "fragment_*.json"))
    if not fragments:
        print(
            f"{AC_PREFIX} Warning: No worker fragments found in {report_dir}. "
            "Check if your code actually executed any instrumented tools or prompts."
        )
        return

    for frag_path in fragments:
        try:
            with open(frag_path, "r", encoding="utf-8") as f:
                fragment_data = json.load(f)
                registry.merge(fragment_data)
            # Remove the fragment after a successful merge to keep the workspace clean
            os.remove(frag_path)
        except Exception as e:
            print(f"{AC_PREFIX} Error merging fragment {frag_path}: {e}")

    # 3. Generate Final Consolidated Report
    # This creates the unified coverage.xml (Cobertura) and index.html.
    generate_report(
        output_dir=report_dir, xml_file="coverage.xml", source_dir=source_dir
    )
    print(
        f"{AC_PREFIX} Success: Consolidated report generated in {report_dir}/index.html"
    )


def main() -> None:
    """Main CLI execution logic."""
    parser = argparse.ArgumentParser(
        description="AgentCover: LLM Prompt and Tool Coverage Tool.", prog="agent-cover"
    )
    subparsers = parser.add_subparsers(dest="action", required=True)

    # 'run' command configuration
    run_parser = subparsers.add_parser(
        "run", help="Run a command with coverage instrumentation."
    )
    run_parser.add_argument(
        "--source-dir",
        default=".",
        help="Root directory of the source code (default: current directory).",
    )
    run_parser.add_argument(
        "--report-dir",
        default="agent_coverage_report",
        help="Directory to store reports and fragments.",
    )
    run_parser.add_argument(
        "command_args",
        nargs=argparse.REMAINDER,
        help="The command to execute (e.g., -- pf run ...).",
    )

    args = parser.parse_args()

    # Handle the remainder arguments correctly (remove the '--' separator if present)
    cmd = args.command_args
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]

    if not cmd:
        print("{AC_PREFIX} Error: No target command provided.", file=sys.stderr)
        sys.exit(1)

    # Normalize paths for cross-process consistency
    source_dir = os.path.abspath(args.source_dir)
    report_dir = os.path.abspath(args.report_dir)

    # Setup temporary bootstrap environment
    temp_dir = tempfile.mkdtemp(prefix="ac_bootstrap_")
    sitecustomize_path = os.path.join(temp_dir, "sitecustomize.py")

    try:
        # Write the sitecustomize.py script that child processes will load
        with open(sitecustomize_path, "w", encoding="utf-8") as f:
            f.write(
                BOOTSTRAP_TEMPLATE.format(report_dir=report_dir, source_dir=source_dir)
            )

        # Prepare the environment with injected PYTHONPATH
        env = os.environ.copy()
        current_pp = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            f"{temp_dir}{os.pathsep}{current_pp}" if current_pp else temp_dir
        )

        # Prevent Python from writing .pyc files in the temp directory
        env["PYTHONDONTWRITEBYTECODE"] = "1"

        print(f"{AC_PREFIX} Launching command: {' '.join(cmd)}")

        # Execute the target command (e.g., PromptFlow, Pytest, or raw script)
        # We pass our modified environment to ensure children are instrumented.
        result = subprocess.run(cmd, env=env)

        # Post-execution aggregation
        # We run this even if the command failed to capture partial coverage results.
        aggregate_and_report(report_dir, source_dir)

        sys.exit(result.returncode)

    finally:
        # Strict cleanup of the bootstrap temporary directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    main()
