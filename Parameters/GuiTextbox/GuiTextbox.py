from Parameter import Parameter

class GuiTextbox(Parameter):
    struct = 'u'  # utf8
    
    def __init__(self, *, name: str = "", initial_value=False, **k):
        super().__init__(name=name, **k)
        self.name = name
        self.state = initial_value
        
    def __call__(self, state, gui=False):
        # gui means that it was sent from the websocket and do not echo. still need to figure out how to make multiple pages work. 
        if isinstance(state, bytearray):
            state = state.decode("utf8")
        super().__call__(state)
        if not gui:
            self.iris.bifrost.send(self.pid, self.state)

    def gui(self):
        return {"name": self.name, "pid": self.pid, "initial_value":self.state, "type": "GuiTextbox"}
    