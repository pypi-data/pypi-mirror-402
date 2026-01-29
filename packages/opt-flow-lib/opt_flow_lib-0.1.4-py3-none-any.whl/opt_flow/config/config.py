from multiprocessing import Value
from typing import Dict, Any, TYPE_CHECKING
from time import time as time_calc
if TYPE_CHECKING:
    from opt_flow.acceptance import BaseAcceptance
    
class Config:
    
    """
    Singleton class for global configuration and state in the optimization framework.

    This class stores configuration flags, IDs, random seeds, timing information,
    parallelization state, and default acceptance criteria. It ensures thread-safe
    access for IDs when running in parallel.

    The singleton instance is available as `config`.
    """
    
    
    _instance = None
    
    def __init__(self):
        self._debug_validation: bool = True
        self._replay: bool = False
        self._start_time: float = time_calc()
        self._track: bool = False
        self._ls_id = 0
        self._imp_id = 0
        self._alg_id = 0
        self._seed = 0
        self._default_acceptance = None
        self._parallel = False
        self._name = ""
        
    def to_dict(self) -> Dict[str, Any]:
        return {"debug_validation": self._debug_validation,
                "replay": self._replay,
                "imp_id": self._imp_id,
                "ls_id": self._ls_id,
                "start_time": self._start_time,
                "seed": self._seed,
                "default_acceptance": self._default_acceptance,
                "parallel": self._parallel,  
                "name": self._name,       
                "track": self._track  
                }
        
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    @property
    def debug_validation(self) -> bool:
        """bool: Whether to run internal validation checks."""
        return self._debug_validation
    
    @property
    def name(self) -> str:
        """str: name of the algorithm"""
        return self._name
    
    @property
    def seed(self) -> int:
        """int: Random seed used for reproducibility."""
        return self._seed
    
    @property
    def track(self) -> bool:
        """bool: Whether algorithm stats are tracked each iteration."""
        return self._track
    
    @property
    def parallel(self) -> bool:
        """bool: Whether parallel execution is enabled."""
        return self._parallel
    
    @property
    def default_acceptance(self) -> "BaseAcceptance":
        """
        BaseAcceptance: The default acceptance strategy.

        Raises:
            RuntimeError: If no default acceptance is configured.
        """
        if self._default_acceptance is None:
            raise RuntimeError("Must configure a default acceptance.")
        return self._default_acceptance
    
    @property
    def start_time(self) -> bool:
        """float: Timestamp when the configuration (or run) started."""
        return self._start_time
    
    @property
    def replay(self) -> bool:
        """bool: Whether to replay a previous run."""
        return self._replay
    
    @property
    def ls_id(self) -> int:
        if self._parallel:
            with self._ls_id.get_lock():
                return self._ls_id.value
        else:
            return self._ls_id
        
    
    @property
    def imp_id(self) -> int:
        if self._parallel:
            with self._imp_id.get_lock():
                return self._imp_id.value
        else:
            return self._imp_id
        
        
    @property
    def alg_id(self) -> int:
        if self._parallel:
            with self._alg_id.get_lock():
                return self._alg_id.value
        else:
            return self._ls_id
    
    
    def _increment_ls_id(self):
        if self._parallel:
            with self._ls_id.get_lock():
                self._ls_id.value += 1
        else:
            self._ls_id += 1
        
    def _increment_imp_id(self):
        if self._parallel:
            with self._imp_id.get_lock():
                self._imp_id.value += 1
        else:
            self._imp_id += 1
            
    def _increment_alg_id(self):
        if self._parallel:
            with self._alg_id.get_lock():
                self._alg_id.value += 1
        else:
            self._alg_id += 1

    @debug_validation.setter
    def debug_validation(self, value: bool):
        if not isinstance(value, bool):
            raise ValueError("debug_validation must be a boolean")
        self._debug_validation = value
        
    @track.setter
    def track(self, value: bool):
        if not isinstance(value, bool):
            raise ValueError("track must be a boolean")
        self._track = value
        
    @name.setter
    def name(self, value: str):
        if not isinstance(value, str):
            raise ValueError("name must be a string")
        self._name = value
        

    @start_time.setter
    def start_time(self, value: float):
        if not isinstance(value, (int, float)):
            raise ValueError("start_time must be numeric")
        self._start_time = value

    @parallel.setter
    def parallel(self, value: bool):
        if not isinstance(value, bool):
            raise ValueError("parallel must be a boolean")
        self._parallel = value
        if value:
            if isinstance(self._ls_id, int):
                self._ls_id = Value('i', self._ls_id)
            if isinstance(self._imp_id, int):
                self._imp_id = Value('i', self._imp_id)
            if isinstance(self._alg_id, int):
                self._alg_id = Value('i', self._alg_id)
        
    @default_acceptance.setter
    def default_acceptance(self, value: "BaseAcceptance"):
        from opt_flow.acceptance import BaseAcceptance
        if not isinstance(value, BaseAcceptance):
            raise ValueError("default_acceptance must be a BaseAcceptance")
        self._default_acceptance = value
        
    @seed.setter
    def seed(self, value: int):
        if not isinstance(value, int):
            raise ValueError("seed must be an integer")
        self._seed = value
        
    @replay.setter
    def replay(self, value: bool):
        if not isinstance(value, bool):
            raise ValueError("replay must be a boolean")
        self._replay = value
        
    @alg_id.setter
    def alg_id(self, value: int):
        self._alg_id = value
            
    @imp_id.setter
    def imp_id(self, value: int):
        self._imp_id = value

            
    @ls_id.setter
    def ls_id(self, value: int):
        self._ls_id = value
        



config = Config()


def configure(last_conf: Dict[str, Any]):
    """
    Update the global configuration using a dictionary.

    Args:
        last_conf (Dict[str, Any]): Dictionary containing configuration
            attributes and their new values. Keys should match Config properties.
    """
    for attr, value in last_conf.items():
        setattr(config, attr, value)
        
        
from contextlib import contextmanager
from typing import Optional


@contextmanager
def override_config(seed: Optional[int] = None,
                     default_acceptance = None,
                     parallel: Optional[bool] = None,
                     track = False,
                     name: str = ''):
    """
    Temporarily override global configuration values.

    Args:
        seed (int, optional): Temporary random seed.
        default_acceptance (BaseAcceptance, optional): Temporary default acceptance.
        parallel (bool, optional): Temporary parallel mode.
    """
    # Save old values
    old_seed = config.seed
    old_acceptance = config._default_acceptance
    old_parallel = config.parallel
    old_start_time = config.start_time
    old_name = config.name
    old_track = config.track

    try:
        # Set new values if provided
        if seed is not None:
            config.seed = seed
        if default_acceptance is not None:
            config.default_acceptance = default_acceptance
        if parallel is not None:
            config.parallel = parallel
        config.name = name
        config.track = track
        config.start_time = time_calc()

        yield  # Control goes to the with-block

    finally:
        # Restore old values
        config.seed = old_seed
        config._default_acceptance = old_acceptance
        config.parallel = old_parallel
        config.start_time = old_start_time
        config.name = old_name
        config.track = old_track
        
        