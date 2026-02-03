from Parameter import Parameter
from floe import make_var

class GuiUsbCamera(Parameter):
    struct = 'H'  # unint16
    
    def __init__(self, *, name: str = "", record: bool=False, save_file=None, **k):
        super().__init__(name=name, **k)
        self.name = name
        self.record = make_var(record)
        self.save_file = make_var(save_file)
    
    def update(self):
        super().update()
        self.record.add_hot(self._set_record)
        self.save_file.add_hot(self._do_save_file)
    
    def _set_record(self, state):
        data = {'cmd': 'set_record', 'state': state}
        self.iris.bifrost.send(self.pid, data)
        
    def _do_save_file(self, *args):
        data = {'cmd': 'save_file'}
        if isinstance(args[0], str):
            data['filename'] = args[0]
        self.iris.bifrost.send(self.pid, data)
                
    def __call__(self, state, gui=False):
        # gui means that it was sent from the websocket and do not echo. still need to figure out how to make multiple pages work. 
        if gui:
            state = int(state.decode('utf8'))
        super().__call__(state)
        # print(self.name, self.state)
        if not gui:
            self.iris.bifrost.send(self.pid, self.state)
       
    def gui(self):
        return {"name": self.name, "pid": self.pid, "type": "GuiUsbCamera"}
    