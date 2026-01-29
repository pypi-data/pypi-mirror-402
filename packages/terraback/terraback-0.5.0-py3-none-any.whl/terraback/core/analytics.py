"""
Analytics tracking module for terraback CLI.

This module provides stub functions for analytics tracking.
Currently implements no-op functions as analytics infrastructure is not yet configured.
"""

from typing import Any


def track_command(command: str, *args: Any, **kwargs: Any) -> None:
    """
    Track CLI command execution.

    Args:
        command: Name of the command being executed
        *args: Additional positional arguments
        **kwargs: Additional keyword arguments (e.g., success, duration, error)

    Note:
        Currently a no-op stub. Will be implemented when analytics infrastructure is configured.
    """
    pass


def track_event(event: str, *args: Any, **kwargs: Any) -> None:
    """
    Track custom events within the CLI.

    Args:
        event: Name of the event being tracked
        *args: Additional positional arguments
        **kwargs: Additional keyword arguments (e.g., properties, metadata)

    Note:
        Currently a no-op stub. Will be implemented when analytics infrastructure is configured.
    """
    pass
