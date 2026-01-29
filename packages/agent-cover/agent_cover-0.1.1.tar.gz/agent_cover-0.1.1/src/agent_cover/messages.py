"""Centralized logging utilities for AgentCover instrumentation.

This module acts as the **Single Source of Truth** for log messages emitted during
the instrumentation process. It standardizes how the library reports events,
errors, and skipped targets.

AgentCover adopts a **"Best Effort"** instrumentation strategy. It attempts to patch
various third-party libraries (LangChain, PromptFlow, etc.) across many versions.
Consequently, some targets will inevitably be missing in a specific user environment.
"""

import logging


class InstrumentationLogger:
    """Centralized logging helper for Instrumentation logic."""

    @staticmethod
    def log_skip_missing_module(logger: logging.Logger, mod_name: str):
        """Log in DEBUG if a module is not found."""
        msg = (
            f"Skipping instrumentation for target '{mod_name}': "
            "Module not found (likely a version mismatch)."
        )
        logger.debug(msg)

    @staticmethod
    def log_skip_missing_attr(logger: logging.Logger, mod_name: str, attr_name: str):
        """Log in DEBUG when skipping a missing attribute."""
        msg = (
            f"Skipping '{attr_name}' in '{mod_name}': "
            "Attribute not found in this version."
        )
        logger.debug(msg)

    @staticmethod
    def log_import_error(logger: logging.Logger, mod_name: str, error: Exception):
        """Log WARNING if module exists but import fails."""
        msg = f"Could not import existing module '{mod_name}': {error}"
        logger.warning(msg)
