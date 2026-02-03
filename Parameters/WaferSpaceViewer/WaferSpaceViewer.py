from Parameter import Parameter
from floe import make_var
import json

class WaferSpaceViewer(Parameter):
    struct = 'H'  # unint16
    
    def __init__(self, **k):
        super().__init__(**k)
    
    # def update(self):
    #     super().update()
    #     self.speed.add_hot(self.set_speed)
    #     self.start.add_hot(self._start)
    #     self.stop.add_hot(self._stop)
    #     self.reset.add_hot(self._reset)
    
    
    def gui(self):
        return {"name": self.name, "pid": self.pid, "state": self.state, "type": "WaferSpaceViewer"}
    