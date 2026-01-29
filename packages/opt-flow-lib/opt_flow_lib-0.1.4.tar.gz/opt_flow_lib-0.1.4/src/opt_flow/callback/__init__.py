"""
This module defines the callback infrastructure for the opt_flow framework.

Callbacks allow users to hook into the execution of metaheuristic algorithms
to monitor progress, collect statistics, or implement custom behaviors
at specific execution points.

"""

from opt_flow.callback.base.callback import Callback
from opt_flow.callback.base.callback_args import CallbackArgs

__all__ = ["Callback", "CallbackArgs"]