import json

from Parameter import Parameter
from floe import make_var
import json

class WaferspaceMoveGenerator(Parameter):
    struct = 'str'  
    
    def __init__(self, **k):
        super().__init__(**k)
        self.state = ""
        self.CLEAR_Z = 5.0
        self.PICK_Z = -1.0
        self.tape_location = (200.0, -200.0, 0.0)  # X,Y,A location of tape start

    def __call__(self, state, **k):
        self.state = state
        self.state = "\n".join(json.dumps(cmd) for cmd in self.gen())
        self.send()

    def _place(self, x, y, a):
        yield {'cmd': 'comment', 'data': f"placing at: X{x} Y{y}"}
        yield dict(cmd='move', x=x, y=y, f=10000)
        yield {'cmd': 'sleep', 'seconds': .1}
        yield dict(cmd='move', z=self.PICK_Z, f=4500)
        yield {'cmd': 'eval', 'eval': 'suck(True)'}
        yield {'cmd': 'sleep', 'seconds': .5}
        yield dict(cmd='move', z=self.CLEAR_Z, f=12500)

    def _pick(self, x, y):
        yield {'cmd': 'comment', 'data': f"picking at: X{x} Y{y}"}
        yield dict(cmd='move', x=x, y=y-200, f=10000) # TODO: hack work offset
        yield {'cmd': 'sleep', 'seconds': .1}
        yield dict(cmd='move', z=self.PICK_Z, f=4500)
        yield {'cmd': 'eval', 'eval': 'suck(False)'}
        yield {'cmd': 'sleep', 'seconds': .5}
        yield dict(cmd='move', z=self.CLEAR_Z, f=12500)

    def alert(self, alert_msg: str):
        cmd = {"cmd": "alert", "alert": alert_msg}
        self.iris.bifrost.send(self.pid, cmd)
    
    def do_die(self, location):
        yield from self._pick(location[0], location[1]) # pick from wafer
        yield from self._place(*self.tape_location) # place in tape
    
    def gen(self):
        if not isinstance(self.state, list):
            state = self.state.splitlines()
        else:
            state = self.state
        
        for line in state:
            order = json.loads(line)
            if order['cmd'] == "do_die":
                yield from self.do_die(order['location'])
            else:
                yield order

    def gui(self):
        return {"name": self.name, "pid": self.pid, "state": self.state, "type": "WaferspaceMoveGenerator"}