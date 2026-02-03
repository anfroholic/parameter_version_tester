from floe import FP, PID, Stater
from iris import Iris
import os, json

# blob constants
ACTIVE = 1
SND2OB = 2
SND2IIB = 4
DBG_SRL = 8
HOT = 16
PARTIAL = 32
ALIAS = 64
LOGGING = 128

class Parameter:  # Abstract class
    datatypes = {
        'bool': '?',
        'byte': 'b',
        'unbyte': 'B',
        'int16': 'h',
        'unint16': 'H',
        'int': 'i',
        'unint': 'I',
        'int64': 'q',
        'unint64': 'Q',
        'float': 'f',
        'double': 'd',
        'bytes': 'e',
        'utf8': 'u',
        'string': 'u',
        'nibble': 'u',
        'rgb': '3B',
        'JSON': 'j',
        'json': 'j'
    }
    
    
    # __slots__ = ('pid', 'state', 'struct', 'p', 'iris', 'blob', 'hot')
    def __init__(self, *, pid: int=0, iris: Iris, state: any = None, name=None, active=False, debug=False, bcast=False, **k):
        self.pid = int(pid)
        self.state = state

        self.p = iris.p
        self.iris = iris

        # blob package: [hot, debug, broadcast(self), broadcast(bus), active] >>>LSB
        self.blob = 0
        if active:
            self.blob |= ACTIVE
        if debug:
            self.blob |= DBG_SRL
        if bcast:
            self.blob |= SND2OB

        self.hot = None
        # self.partial = None
        # self.alias = None
        
        iris.p[self.pid] = self
        
        
        self.name = name
        if name is not None and name != 'no_name':
            iris.locals[name] = self
            
        print(f"{self.name}:\n    {self.__class__.__name__}, pid:{self.pid}")

    # ------------------------------------------------------------------------

    def __call__(self, state) -> None:
        self.state = state
        # print(f'current state is {self.state}')
        self.send()

    def update(self):
        for attr, val in self.__dict__.items():            
            if isinstance(val, FP):
                setattr(self, attr, self.iris.p[val.pid])

    def _load_save_data(self):
        # helper function for loading save data
        if 'savedata' not in os.listdir():
            return
        if f'{self.pid}.json' in os.listdir('savedata'):
            with open(f'savedata/{self.pid}.json', 'r') as savedata:
                return json.load(savedata)
        
    
    def save(self):
        # still not sure how I want to implement saves. 
        # should there be a global method or should they be param specific
        pass
    
    def _save(self, data: dict):
        import os, json
        if 'savedata' not in os.listdir():
            os.mkdir('savedata')
        with open(f'savedata/{self.pid}.json', 'w') as f:
            json.dump(data, f)
            
        # this could be another way
        # ignore = {'iris', 'pid', 'p', 'funcs'}
        # assets = {}
        # for name, attr in self.__dict__.items():
        #     if name not in ignore:
        #         if isinstance(attr, Parameter):
        #             continue
        #         if isinstance(attr, Stater):
        #             assets[name] = attr.state
        #         else:
        #             assets[name] = attr
        # return assets
    
    def add_hot(self, hot: any):  # int | str | callable
        """add internal subscription, usually called by the subscriber"""
        self.blob |= HOT
        if isinstance(hot, str):
            hot = self.p[int(hot)]
        elif isinstance(hot, int):
            hot = self.p[hot]
        
        if self.hot:
            if isinstance(self.hot, tuple):
                _hot = list(self.hot)
                _hot.append(hot)
                self.hot = tuple(_hot)
            else:
                self.hot = (self.hot, hot)
        else:
            self.hot = hot
            
    def remove_hot(self, param):
        print('param', param, self.hot)
        if self.hot is param: # param is only hot route
            self.hot = None
            self.blob ^= HOT
        if isinstance(self.hot, tuple):     
            if param in self.hot:
                hot = list(self.hot)
                hot.remove(param)
                self.hot = tuple(hot)
    
    @property
    def active(self):
        return self.blob & ACTIVE
        
        
    def gui(self):
        return None
        
    # ------------------------------------------------------------------------

    def send(self, cmd=0, pid=None, adr=None) -> None:
        if self.blob & ACTIVE:  # ACTIVE
            if self.blob & SND2OB:  # SEND TO OUTBOX
                if pid is None:
                    pid = self.pid
                self.iris.send(pid=pid,
                               load=self.iris.msg.bundle(self.state, self.struct),
                               type=cmd,
                               adr=adr)
            # if self.blob & SND2IIB:  # YIELD
            #     self.iris.send_i((self.pid, self.state))
            if self.blob & DBG_SRL:  # DEBUG SERIAL
                msg = f'DEBUG: pid: {self.pid}, state: {self.state}'
                if self.iris.bifrost.active():
                    self.iris.bifrost.post(msg)
                else:
                    print(msg)

            if self.blob & HOT:  # CALL param
                if isinstance(self.hot, tuple):
                    for h in self.hot:
                        h(self.state)  # h = Parameter
                else:
                    self.hot(self.state)

            # if self.blob & LOGGING:
            #     print(f'MAKE LOGGER: pid: {self.pid}, state: {self.state}')


    

