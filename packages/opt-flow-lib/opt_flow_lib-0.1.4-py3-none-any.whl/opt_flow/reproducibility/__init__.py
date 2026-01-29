"""
Reproducibility Utilities for Iterations Registry

This module provides functionality to save and load the state of the
iterations registry used during algorithm executions. This allows users
to reproduce previous runs, resume experiments, or analyze past executions.

Functions
---------
save_execution(filename: str | None = None)
    Saves the current state of the iterations registry to a JSON file.

load_execution(filename: str)
    Loads a previously saved iterations registry from a JSON file and
    enables replay mode.
"""

from opt_flow.reproducibility.iterations_registry import load_execution, save_execution


__all__ = ["load_execution", "save_execution"]