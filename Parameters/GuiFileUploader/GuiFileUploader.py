from Parameter import Parameter

class GuiFileUploader(Parameter):
    struct = 'e'  # bool
    
    def __init__(self, *, name: str = "", **k):
        super().__init__(name=name, **k)
        self.name = name
        
        element = {"name": name, "pid": self.pid, "type": "GuiFileUploader"}
        self.iris.webstuff.append(element)
    
    def __call__(self, state, gui=False):
        # super().__call__()
        self.state = state
        # print(self.name, self.state)
        if not gui:
            self.iris.bifrost.send(self.pid, self.state)
        if self.hot:
            if type(self.hot) is tuple:
                for h in self.hot:
                    h(self.state)  # h = Parameter
            else:
                self.hot(self.state)

    def gui(self):
        return {"name": self.name, "pid": self.pid, "type": "GuiFileUploader"}
    