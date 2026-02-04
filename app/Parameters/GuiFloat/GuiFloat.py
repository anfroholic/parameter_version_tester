from Parameter import Parameter

class GuiFloat(Parameter):
    struct = 'f'  # float
    
    def __init__(self, *, name: str = "", initial_value=0, **k):
        super().__init__(name=name, **k)
        self.name = name
        self.state = float(initial_value)
        
    def __call__(self, state, gui=False):
        # gui means that it was sent from the websocket and do not echo. still need to figure out how to make multiple pages work. 
        if gui:
            state = float(state)
        
        super().__call__(state)
        if not gui:
            self.iris.bifrost.send(self.pid, self.state)

    def gui(self):
        return {"name": self.name, "pid": self.pid, "initial_value":self.state, "type": "GuiFloat"}
    