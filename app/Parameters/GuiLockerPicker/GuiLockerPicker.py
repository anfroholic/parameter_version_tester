from Parameter import Parameter
from floe import make_var
import json
try:
    import uasyncio as asyncio
except:
    import asyncio
import gc    


class GuiLockerPicker(Parameter):
    struct = 'i'  # int
    
    def __init__(self, *, name: str = "", pod=False, heartbeat: bool=False, heartbeat_interval: int=10000, websocket: str="", **k):
        super().__init__(name=name, **k)
        self.name = name
        self.hbt = heartbeat
        self.hbt_int = heartbeat_interval
        if pod:
            self.pod = make_var(pod)
        else:
            self.pod = make_var({})
        self.num_feeders = 0
        self.funcs = {
            'update_locker': self.update_locker,
            'choose_locker': self.choose_locker,
            'get_locker': self.get_locker,
        }
        self.websocket = f"{websocket}?locker_pod={self.name}" if websocket else ""
        

    
    def update(self):
        super().update()

        if self.hbt:
            loop = asyncio.get_event_loop()
            loop.create_task(self.chk())
        
    async def chk(self):
        while True:
            self.state = self.pod.state
            self.send()
            await asyncio.sleep(self.hbt_int/1000)
        
    def __call__(self, state, gui=False):
        if isinstance(state, bytes):
            state = json.loads(state.decode())
        if isinstance(state, str):
            state = json.loads(state)
        if state['cmd'] in self.funcs:
            self.funcs[state['cmd']](state)
        else:
            print("TODO: make unhanging exception thing")

    
    def update_locker(self, address, state):
        for row in self.pod.state:
            for locker in row:
                if locker['address'] == address:
                    locker.update(state)  
        
    def choose_locker(self, state):
        # message says that *user* wants to now choose a locker
        # this will enable the 'claim' buttons on the gui
        # repl test Neverland_pod_1({'cmd': 'choose_locker', 'user': 'user1'})
        self.iris.bifrost.send(self.pid, state)

    def get_locker(self, state):
        # rent this locker
        msg = {
            'cmd': 'update_locker', 
            'name': state['user'], 
            'status': 'full', 
            'address': state['address'], 
            'days': 3,
            'timeRemaining': 259200, # 3 days
            }
        self.update_locker(state['address'], msg)
        self.send()
        self.iris.bifrost.send(self.pid, msg) 
        
    def empty_locker(self, address):
        empty_locker = dict(
            name='',
            status='empty',
            address=address
        )
        self.update_locker(address=address, state=empty_locker)
    def _empty_all_full(self):
        """empty all tables with status full"""
        gc.collect()
        for row in self.pod.state:
            for locker in row:
                if locker['status'] == 'full':
                    adr = locker['address']
                    locker.update(dict(name='', status='empty', address=adr))
        self.state = self.pod.state
        self.render_table()
        gc.collect()

    def render_table(self):
        """repopulate the entire table"""
        msg = {
            'cmd': 'render_table',
            'pod': self.state
        }
        gc.collect()
        self.iris.bifrost.send(self.pid, msg)

    def gui(self):
        return {"name": self.name, "pid": self.pid, "pod": self.pod.state, "websocket": self.websocket, "type": "GuiLockerPicker"}
    