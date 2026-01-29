"""
This module provides global configuration utilities for the opt_flow framework.

It defines a configuration object and helper functions that control
global execution settings such as parallelism, reproducibility, and
framework-wide behavior.

"""

from opt_flow.config.config import Config, configure, config, override_config

__all__ = ["Config", "configure", "config", "override_config"]