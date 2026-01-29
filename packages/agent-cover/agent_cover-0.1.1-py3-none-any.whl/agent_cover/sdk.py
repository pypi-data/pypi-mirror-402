"""Main entry point for the AgentCover SDK.

This module provides high-level functions to manually control the coverage process outside
of a standard pytest environment (e.g., in a custom script or a notebook).

It is designed to handle complex execution models, including multi-process environments
like Microsoft PromptFlow. It orchestrates the initialization of instrumentors,
manages signals and hooks for distributed workers, and handles data persistence
via JSON fragments and consolidated reports.

Exposed Functions:
    - [`start_coverage`][agent_cover.sdk.start_coverage]: Initializes and starts tracking.
    - [`generate_report`][agent_cover.sdk.generate_report]: Dumps the results to HTML/XML.

## SDK Usage Example

If you want to run coverage for a script and automatically generate a report on exit:

```python
from agent_cover.sdk import start_coverage

if __name__ == "__main__":
    # 1. Start coverage (registers atexit hooks for reporting)
    start_coverage(
        source_dir="src",
        report_dir="reports/agent-cover",
        auto_save=True
    )

    # 2. Run your code
    run_my_agent_logic()

    # When the script ends, reports are generated automatically.

```
"""

import atexit
import json
import logging
import os
import signal
import sys
from typing import Any, Optional

from .config import get_config, load_config
from .discovery import discover_repository_modules
from .instrumentation import (
    instrument_all,
    scan_static_definitions,
)
from .registry import registry
from .reporting.html import generate_html_report
from .reporting.xml import generate_cobertura_xml

logger = logging.getLogger(__name__)

# --- GLOBAL STATE FOR WORKER COORDINATION ---

# Prevents redundant signal handler registration
_HANDLERS_ARMED = False

# Stores configuration to be accessible during signal-triggered flushes
_CONFIG_STORE = {"report_dir": "agent_coverage_report", "source_dir": os.getcwd()}


def _save_report_logic() -> None:
    """Internal logic to persist coverage data to disk.

    In a multi-process environment (e.g., PromptFlow workers), this function
    saves a JSON fragment containing the process's local hits. This allows the
    parent CLI to aggregate results later. It also generates an individual
    XML report for the current process as a fallback.
    """
    if not registry.executions:
        return

    pid = os.getpid()
    report_dir = os.path.abspath(_CONFIG_STORE["report_dir"])
    source_dir = _CONFIG_STORE["source_dir"]

    try:
        os.makedirs(report_dir, exist_ok=True)
    except OSError:
        pass  # Handle potential race conditions in directory creation

    # 1. Save JSON Fragment for CLI aggregation
    # Fragments are essential because PromptFlow workers are often terminated
    # before they can perform a clean exit.
    fragment_path = os.path.join(report_dir, f"fragment_{pid}.json")
    try:
        fragment_data = {
            "executions": list(registry.executions),
            "definitions": registry.definitions,
            "decision_hits": {k: list(v) for k, v in registry.decision_hits.items()},
        }
        with open(fragment_path, "w", encoding="utf-8") as f:
            json.dump(fragment_data, f)
        logger.debug(f"Worker {pid}: Coverage fragment saved to {fragment_path}")
    except Exception as e:
        # We use sys.__stderr__ as a fallback because standard logging
        # might be suppressed or captured during process shutdown.
        if sys.__stderr__:
            sys.__stderr__.write(
                f"[AgentCover] Worker {pid} fragment save failed: {e}\n"
            )

    # 2. Save Individual XML/HTML Reports
    # Useful for immediate inspection of specific worker activity.
    try:
        xml_filename = f"coverage_{pid}.xml"
        generate_report(
            output_dir=report_dir, xml_file=xml_filename, source_dir=source_dir
        )
    except Exception as e:
        logger.error(f"Worker {pid}: Individual report generation failed: {e}")


def arm_worker_handlers() -> None:
    """Arms signal handlers and atexit hooks for the current process.

    This ensures that coverage data is flushed to disk when the process
    receives a termination signal (SIGTERM) or exits normally. This is
    critical for PromptFlow workers on Linux/WSL.
    """
    global _HANDLERS_ARMED
    if _HANDLERS_ARMED:
        return
    _HANDLERS_ARMED = True

    def _termination_handler(signum: int, frame: Any) -> None:
        """Handles external termination signals."""
        logger.debug(
            f"Process {os.getpid()} received signal {signum}. Flushing coverage..."
        )
        _save_report_logic()
        # Exit to allow the parent orchestrator to continue
        sys.exit(0)

    # Register handlers for common termination signals used by orchestrators
    try:
        signal.signal(signal.SIGTERM, _termination_handler)
        signal.signal(signal.SIGINT, _termination_handler)
    except (ValueError, OSError):
        # signal.signal only works in the main thread.
        pass

    # Also register for normal python exit
    atexit.register(_save_report_logic)


def start_coverage(
    source_dir: Optional[str] = None,
    report_dir: str = "agent_coverage_report",
    auto_save: bool = True,
    **kwargs: Any,
) -> None:
    """Initializes and starts the coverage tracking session.

    This function sets up the configuration, instruments supported libraries,
    and performs static discovery of project assets (Prompts, Tools, Flows).
    It is suitable for manual instrumentation in scripts or distributed worker processes.

    Args:
        source_dir (Optional[str]): The root directory of the source code to cover.
            Defaults to the current working directory.
        report_dir (str): The directory where coverage reports and fragments will be saved.
            Defaults to "agent_coverage_report".
        auto_save (bool): If True, enables immediate flushing on hits and registers
            atexit/signal hooks to generate reports automatically when the process finishes.
        atexit_registrar (Optional[Callable]): Dependency injection for testing exit registration.
        **kwargs: Additional parameters like `is_worker` to identify sub-processes
            in multiprocessing environments (e.g., PromptFlow workers).

    Examples:
        **Basic Usage:**
        ```python
        from agent_cover.sdk import start_coverage

        # Start tracking and auto-save on exit
        start_coverage(source_dir="./src")

        # Run your agent logic...
        ```
    """
    # 1. Update internal configuration store
    if source_dir:
        _CONFIG_STORE["source_dir"] = os.path.abspath(source_dir)
    if report_dir:
        _CONFIG_STORE["report_dir"] = os.path.abspath(report_dir)

    root = _CONFIG_STORE["source_dir"]
    if root not in sys.path:
        sys.path.insert(0, root)

    # 2. Setup environment and instrument targets
    load_config(root)
    instrument_all()

    # 3. PromptFlow specific initialization
    # Workers need to scan definitions to map runtime Jinja2 hashes to filenames.
    from .instrumentation.promptflow import (
        instrument_promptflow,
        scan_promptflow_definitions,
    )

    try:
        scan_promptflow_definitions(root_path=root)
        instrument_promptflow()
    except Exception as e:
        logger.warning(f"PromptFlow initialization failed: {e}")

    # 4. General Static Discovery
    try:
        discover_repository_modules(root_path=root)
        scan_static_definitions(root_path=root)
    except Exception as e:
        logger.debug(f"Static discovery warning: {e}")

    # 5. Multiprocessing and persistence setup
    if auto_save:
        # If running in a bootstrapped subprocess, enable immediate flush.
        # This prevents data loss if a worker is killed abruptly.
        if "AGENT_COVER_BOOTSTRAPPED" in os.environ or kwargs.get("is_worker"):
            registry.on_hit_callback = _save_report_logic
            logger.debug(
                f"AgentCover: Immediate flush enabled for worker {os.getpid()}"
            )

        arm_worker_handlers()
        logger.info(
            f"AgentCover session started. Reports will be saved to {report_dir}"
        )


def generate_report(
    output_dir: str = "coverage_report",
    xml_file: str = "coverage.xml",
    source_dir: Optional[str] = None,
) -> None:
    """Generates the final coverage reports (HTML and Cobertura XML).

    Args:
        output_dir (str): Directory where the reports will be saved.
        xml_file (str): Filename for the XML Cobertura report.
        source_dir (str, optional): If provided, triggers a re-scan of definitions.
    """
    if source_dir:
        try:
            scan_static_definitions(root_path=source_dir)
        except Exception:
            pass

    config = get_config()
    os.makedirs(output_dir, exist_ok=True)

    # Generate HTML summary
    generate_html_report(
        registry.definitions,
        registry.executions,
        output_dir,
        config,
        registry.decision_hits,
    )

    # Generate Cobertura XML for CI/CD integration
    xml_path = os.path.join(output_dir, xml_file)
    generate_cobertura_xml(
        registry.definitions,
        registry.executions,
        config,
        registry.decision_hits,
        xml_path,
    )
