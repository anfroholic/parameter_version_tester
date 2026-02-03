from Parameter import Parameter

class GuiButton(Parameter):
    struct = '?'  # bool
    
    def __init__(self, *, name: str = "", trigger: any=True, message: any="", **k):
        super().__init__(name=name, **k)
        self.name = name
        if trigger == True:
            self.state = True
            self.struct = '?'
        elif trigger == False:
            self.state = False
            self.struct = '?'
        elif trigger == 'None':
            self.state = None
            self.struct = None
        elif trigger == 'string':
            self.state = message
            self.struct = 'u'
        elif trigger == 'int':
            self.state = int(message)
            self.struct = 'i'
        elif trigger == 'float':
            self.state = float(message)
            self.struct = 'f'
            
    
    # override
    def __call__(self, *state, gui=False):
        # super().__call__()
        if not gui:
            self.iris.bifrost.send(self.pid, self.state)
        self.send()
        
    def gui(self):
        return {"name": self.name, "pid": self.pid, "color": "green", "type": "GuiButton"}

    
    