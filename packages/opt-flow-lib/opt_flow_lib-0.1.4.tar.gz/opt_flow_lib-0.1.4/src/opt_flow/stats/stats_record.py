from typing import Optional
from dataclasses import dataclass, field
from opt_flow.structure._base import BaseObjective
from opt_flow.structure import BaseIndividual
import time
@dataclass(slots=True)
class StatsRecord:

    timestamp: float = field(default_factory=time.time, init=False)
    objective: Optional[BaseObjective]
    accepted: Optional[bool] 
    individual: BaseIndividual
    event: str 