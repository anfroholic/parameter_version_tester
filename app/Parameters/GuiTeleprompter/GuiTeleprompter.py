from Parameter import Parameter
from floe import make_var
import json

class GuiTeleprompter(Parameter):
    struct = 'H'  # unint16
    
    def __init__(self, *, start=None, stop=None, reset=None, name: str = "", speed: float=1, initial_value:str="", **k):
        super().__init__(name=name, **k)
        self.name = name
        self.speed = make_var(speed)
        self.state = initial_value
        self.start = make_var(start)
        self.stop = make_var(stop)
        self.reset = make_var(reset)
    
    def update(self):
        super().update()
        self.speed.add_hot(self.set_speed)
        self.start.add_hot(self._start)
        self.stop.add_hot(self._stop)
        self.reset.add_hot(self._reset)
    
    def _start(self, *args, **kwargs):
        self.iris.bifrost.send(self.pid, {'cmd': 'start'})
    
    def _stop(self, *args, **kwargs):
        self.iris.bifrost.send(self.pid, {'cmd': 'stop'})
        
    def _reset(self, *args, **kwargs):
        self.iris.bifrost.send(self.pid, {'cmd': 'reset'})
        
    def set_speed(self, state):
        data = {'cmd': 'set_speed',  'state': self.speed.state}
        self.iris.bifrost.send(self.pid, data)
        
        
    def __call__(self, state: str, gui=False):
        # gui means that it was sent from the websocket and do not echo. still need to figure out how to make multiple pages work. 
        if gui:
            state = state.decode('utf8')
        super().__call__(state)
        # print(self.name, self.state)
        if not gui:
            data = {'cmd': 'set_state', 'state': self.state}
            self.iris.bifrost.send(self.pid, data)

    def gui(self):
        return {"name": self.name, "pid": self.pid, "state": self.state, "speed": self.speed.state, "type": "GuiTeleprompter"}
    