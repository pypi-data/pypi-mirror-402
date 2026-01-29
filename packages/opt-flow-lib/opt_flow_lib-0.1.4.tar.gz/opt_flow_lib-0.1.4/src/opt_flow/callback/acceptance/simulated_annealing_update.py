

from opt_flow.callback.base.callback import Callback 
from opt_flow.callback.base.callback_args import CallbackArgs
from opt_flow.acceptance import SimulatedAnnealingAcceptance

class SimulatedAnnealingUpdate(Callback):
    
    """
    Callback that updates the temperature of a SimulatedAnnealingAcceptance
    instance during optimization.

    The temperature is decreased according to the cooling rate whenever
    a candidate solution is accepted.
    """
    
    def __init__(self, acceptance: SimulatedAnnealingAcceptance):
        """
        Initialize the callback with a simulated annealing acceptance instance.

        Args:
            acceptance (SimulatedAnnealingAcceptance): The acceptance
                object whose temperature will be updated.
        """
        self.acceptance = acceptance

    
    def __call__(self, arg: CallbackArgs):
        """
        Update the temperature of the acceptance object based on the callback event.

        The temperature is reduced by multiplying with the cooling rate,
        but is never allowed to go below the minimum temperature.

        Args:
            arg (CallbackArgs): Object containing context and state for the callback,
                including whether the current candidate solution was accepted.
        """
        if arg.accepted:
            self.acceptance.temperature = max(
                self.acceptance.temperature * self.acceptance.cooling_rate, self.acceptance.min_temperature
            )
