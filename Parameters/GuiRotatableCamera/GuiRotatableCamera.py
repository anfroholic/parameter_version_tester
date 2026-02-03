from Parameter import Parameter
from floe import make_var

class GuiRotatableCamera(Parameter):
    struct = 'H'  # unint16
    
    def __init__(self, *, name: str = "", url, **k):
        super().__init__(name=name, **k)
        self.name = name
        self.url = make_var(url)
        
        
    def __call__(self, state, gui=False):
        # gui means that it was sent from the websocket and do not echo. still need to figure out how to make multiple pages work. 
        if gui:
            state = int(state.decode('utf8'))
        super().__call__(state)
        # print(self.name, self.state)
        if not gui:
            self.iris.bifrost.send(self.pid, self.state)
       
    def gui(self):
        return {"name": self.name, "pid": self.pid, "url": self.url.state, "type": "GuiRotatableCamera"}
    