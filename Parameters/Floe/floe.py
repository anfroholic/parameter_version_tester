import json
try:
    import uasyncio as asyncio
except:
    import asyncio
import struct, gc, sys

PID = int

class Stater:
    def __init__(self, state: any):
        """ stored constant for use when a remote parameter is not wanted """    
        self.state = state
        self.hot = None
        
    def __call__(self, *args, **kwargs) -> None:
        if args:
            self.state = args[0]
        if self.hot:
            if type(self.hot) is tuple:
                for h in self.hot:
                    h(self.state)
            else:
                self.hot(self.state)

    def add_hot(self, hot: callable):
        if self.hot:
            if self.hot is tuple:
                _hot = list(self.hot)
                _hot.append(hot)
                self.hot = tuple(_hot)
            else:
                self.hot = (self.hot, hot)
        else:
            self.hot = hot        
    
class FP:
    '''Future Param, is a holder until all params created then updated with references with update method
    '''
    def __init__(self, pid) -> None:
        self.pid = pid
        
def make_var(item: any) -> Stater | FP:
    """
    Parameter will expect to get value by requesting item.state
    """
    if isinstance(item, FP):
        return item
    return Stater(item)

class Bifrost:
    """ bifrost is the bridge for the gods. busses and other things are shuffled behind the scenes to the websocket"""
    def __init__(self) -> None:
        self.bifrost = []
        self._checked = [] # to be injected once known to be true
        self.funcs = {}
    
    def active(self):
        if self._checked != []:
            return True
        return False
    
    def send(self, pid: int, msg: str | dict):
        if self.active():
            if isinstance(msg, dict):
                msg = json.dumps(msg)
            self.bifrost.append(f'{pid},{msg}')
        else:
            print(f"{msg}")

    def post(self, msg: str):
        self.send('term', msg)

    def write(self, msg:str):
        # method for when std_out is redirected
        if msg == "\n" or msg == "":
            return
        self.send('term', f"print: {msg}")
    
    def any(self) -> bool:
        if self.bifrost != []:
            return True
        return False
    
    def pop(self) -> str: 
        return self.bifrost.pop(0)
        
    # methods below are for cpython, in upython bifrost is handled in server.process_all
    def add_socket(self, manager):
        self.manager = manager
        self._checked = manager.active_connections

    async def chk(self):
        while True:
            if self.any():
                await self.manager.broadcast(self.pop())
            await asyncio.sleep(.01)
            # await asyncio.sleep(.02)
    
    # method for pyscript
    async def pyscript_chk(self, callback, iris, core_type: str):
        import sys
        if core_type == 'py': # pyscript python core type
            # micropython has stdout hardcoded and cannot be changed yet?
            sys.stdout = iris.bifrost
        self._checked = True
        while True:
            if self.any():
                callback(self.pop())
            await asyncio.sleep(.005)

class Implementation:
    def __init__(self):
        imp = sys.implementation
        self.name = imp.name
        self.wasm = False
        
        if self.name == 'micropython':
            self._machine = imp._machine
            if imp._machine == 'JS with Emscripten':
                self.wasm = True
        try:
            if imp._multiarch:
                self.wasm = True
        except AttributeError:
            pass
implementation = Implementation()

### WIP          
class Watchdog:
    """Handles logging, errors, and exceptions with hardware"""
    CRITICAL = 4
    ERROR    = 3
    WARNING  = 2
    INFO     = 1
    DEBUG    = 0
    
    _levels = [
    "DEBUG",
    "INFO",
    "WARN",
    "ERROR",
    "CRIT",
    ]
    
    def __init__(self):
        self.streams = [print] # callable
        self.level = 0
        self.iris = None
    
    def boot(self, iris):
        self.iris = iris
        # check iris for bus
        if self.iris.bus:
            self.streams.append(self.iris.bus.debug)
        if self.iris.bifrost:
            self.streams.append(self.iris.bifrost.post)
    
    def set_level(self, level: int):
        self.level = level
        
    def log(self, level, msg, *args):
        if level >= self.level:
            for stream in self.streams:
                stream("{self._levels[self.level]}: {msg}")
            
    def debug(self, msg, *args):
        self.log(self.DEBUG, msg, *args)

    def info(self, msg, *args):
        self.log(self.INFO, msg, *args)

    def warning(self, msg, *args):
        self.log(self.WARNING, msg, *args)

    def error(self, msg, *args):
        self.log(self.ERROR, msg, *args)

    def critical(self, msg, *args):
        self.log(self.CRITICAL, msg, *args)

    def exc(self, e, msg, *args):
        self.log(self.ERROR, msg, *args)
        sys.print_exception(e, self._stream)

    def exception(self, msg, *args):
        self.exc(sys.exc_info()[1], msg, *args)


### WIP
import io
class OrderReceiver:
    struct = 'e'
    
    def __init__(self, pid, iris):
        self.pid = pid
        self.state = None # ACK
        self.num_bytes = 0
        self.channel = 0  # this is the channel we are receiving on
        self.return_adr = ('adr', 'pid')
        self.len_order = 0 # this will be the length of the order
        self.recving = False
        self.msg_type = 0 # 0 bytes|1 str|2 order
        
        
    def __call__(self, state, *args, **kwargs):
        """
        First message packing
        B return adr
        H return pid
        H len order
        B msg_type:
            0: bytes
            1: uft8 str
            2: order utf8 json
        """
        if not self.recving:
            # begin transmission
            return_adr, return_pid, len_order, msg_type = struct.unpack('BHHB', state)
            self.return_adr = (return_adr, return_pid)
            self.len_order = len_order
            self.recving = True
            gc.collect()
            self.state = io.BytesIO(b"")  # bytearray(len_order)
            self.ack()
        
        elif self.recving:
            self.num_bytes += len(state)
            
            if self.cur_byte == len(self.state):
                # we are done
                self.process()
            else:
                self.ack()    
    
    def process(self):
        val = self.state.getvalue()
        if self.msg_type == 0:
            # bytes
            print(val)
        elif self.msg_type == 1:
            # utf8 string
            print(val.decode())
        elif self.msg_type == 2:
            # utf8 string
            print(json.loads(val.getvalue().decode()))
        
        self.reset()

    def ack(self):
        self.iris.bus.send(adr=self.return_adr[0], 
                            pid=self.return_adr[1],
                            load=b'\x06' #ack
                            )
    
    def reset(self):
        self.state = None
        self.num_bytes = 0
        self.channel = 0  # this is the channel we are receiving on
        self.return_adr = (None, None)
        self.len_order = 0
        self.recving = False
        gc.collect()