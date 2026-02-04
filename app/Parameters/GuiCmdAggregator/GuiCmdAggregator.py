from Parameter import Parameter
import json
class GuiCmdAggregator(Parameter):
    struct = 'u'  # bool
    
    def __init__(self, *, name: str = "", initial_value="", **k):
        super().__init__(name=name, **k)
        self.name = name
        self.state = initial_value

    def gui(self):
        return {"name": self.name, "pid": self.pid, "type": "GuiCmdAggregator", "initial_value": self.state}
        
    def __call__(self, state: str|dict, gui=False):
        # gui means that it was sent from the websocket and do not echo. still need to figure out how to make multiple pages work. 
        if isinstance(state, (list, dict)):
            state = json.dumps(state)
        if self.state:
            state = '\n' + state
        self.state += state 
        if not gui:
            self.iris.bifrost.send(self.pid, self.state)
        self.send()
        
    def clear(self):
        self.state = ""
        self.iris.bifrost.send(self.pid, self.state)

    def state_as_list(self):
        return [json.loads(line) for line in self.state.split('\n')]

    def gen(self):
        start = 0
        state = self.state
        for i, char in enumerate(state):
            if char == '\n':
                yield json.loads(state[start:i])
                start = i + 1
        # Yield the last segment if there's no trailing newline
        if start < len(state):
            yield json.loads(state[start:])
            