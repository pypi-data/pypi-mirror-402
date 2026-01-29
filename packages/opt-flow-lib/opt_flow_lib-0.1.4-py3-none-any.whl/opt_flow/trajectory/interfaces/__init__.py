"""
This module defines encoding and decoding interfaces for trajectory-based
metaheuristic algorithms.

Encoders and decoders are responsible for transforming solutions between
different representations, enabling flexible integration of improvement
operators and neighborhood structures.

"""

from opt_flow.trajectory.interfaces.decoder import Decoder
from opt_flow.trajectory.interfaces.encoder import Encoder


__all__ = ["Encoder", "Decoder"]