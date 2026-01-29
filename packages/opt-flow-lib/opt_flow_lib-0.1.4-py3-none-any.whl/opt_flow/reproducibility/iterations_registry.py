from multiprocessing import Manager
from opt_flow.config import config
import json
from pathlib import Path
from functools import wraps
from opt_flow.stopping import IterationLimitStopping 

REGISTRY = None
_STOPPING_SINGLETONS = {}

def _init_registry(): 
    global REGISTRY
    if REGISTRY is None:
        manager = Manager()
        REGISTRY = manager.dict()


def _register(id: str, iterations: int):
    if not config.replay:
        REGISTRY[id] = iterations


def save_execution(folder: str | None = None):
    """
    Save the current execution registry to a JSON file.

    The registry captures the state of algorithm executions, including
    recorded metrics, identifiers, and other relevant data. Saving the
    registry allows experiments to be reproduced or analyzed later.

    Parameters
    ----------
    filename : str | None, optional
        The filename to save the registry under. If None, a default name
        including a timestamp is generated (e.g., 'execution_20251225_123456.json').

    Notes
    -----
    The file is saved under a 'runs' directory in the current working
    directory. If the directory does not exist, it is created automatically.
    The saved JSON is pretty-printed and sorted for readability.
    """
    snapshot = dict(REGISTRY)

    # Determine run folder
    if folder is None:
        folder = Path("runs") / f"{config.start_time}_{config.name}"
    folder.mkdir(parents=True, exist_ok=True)

    snapshot = dict(sorted(snapshot.items()))

    path = folder / "execution.json"
    path.write_text(json.dumps(snapshot, indent=4, sort_keys=True), encoding="utf-8")
    
def get_execution_snapshot() -> dict:
    """Get the snapshot of the execution registry to be saved.
    
    The registry captures the state of algorithm executions, including
    recorded metrics, identifiers, and other relevant data. Saving the
    registry allows experiments to be reproduced or analyzed later.
    """
    snapshot = dict(REGISTRY)
    return dict(sorted(snapshot.items()))



def load_execution(filename: str):
    """
    Load a previously saved execution registry from a JSON file.

    This restores the state of the registry to match a prior execution,
    enabling experiment replay and reproducibility.

    Parameters
    ----------
    filename : str
        Path to the JSON file containing the saved execution registry.

    Notes
    -----
    After loading, the `config.replay` flag is set to True to indicate
    that the current execution is a replay. The registry is cleared before
    loading new data to ensure consistency.
    """
    _init_registry()
    path = Path(filename)
    data = json.loads(path.read_text(encoding="utf-8"))

    REGISTRY.clear()
    for k, v in data.items():
        REGISTRY[k] = v

    config.replay = True


def _register_execution(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs) -> bool:
        try:
            _init_registry()
            original_stoppings = self._stopping_criterion
            self._increment_execution_id()
            alg_id = self.id
            if config.replay:
                self._stopping_criterion = _get_reproduced_stopping(alg_id)
            result = func(self, *args, **kwargs)
        finally:
            self._stopping_criterion = original_stoppings
            if not config.replay:
                _register(alg_id, self._tracker.get_total_iterations())
        return result

    return wrapper

def _get_reproduced_stopping(id_: int) -> IterationLimitStopping:
    if id_ not in _STOPPING_SINGLETONS:
        _STOPPING_SINGLETONS[id_] = IterationLimitStopping(REGISTRY.get(id_, 0))
    return _STOPPING_SINGLETONS[id_]