class MHConfig:
    def __init__(self):
        self._node_id: int = 0

    @property
    def node_id(self) -> int:
        return self._node_id
        
    def increment_id(self) -> int:
        self._node_id += 1

mhconfig = MHConfig()

