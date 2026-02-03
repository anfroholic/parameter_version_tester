from Parameter import Parameter

class GuiCodeEditor(Parameter):
    struct = 'e'  # bool
    
    def __init__(self, *, name: str = "", initial_value:str = "", **k):
        super().__init__(name=name, **k)
        self.name = name
        self.state = initial_value

    
    def __call__(self, state, gui=False):
        super().__call__(state)
        # print(self.name, self.state)
        if not gui:
            self.iris.bifrost.send(self.pid, self.state)

    def update(self):
        super().update()
        if not isinstance(self.state, str):
            self.state = self.state.state

    def gui(self):
        return {"name": self.name, "pid": self.pid, "state": self.state, "type": "GuiCodeEditor"}
    