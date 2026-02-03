"""
Analog Input for ESP32
"""

from floe import FP, make_var
from Parameter import Parameter

try:
    import uasyncio as asyncio
except:
    import asyncio    

import sys

f_req = None
_machine = None
imp = sys.implementation
if imp.name == 'cpython':
    _machine = 'cpython'
    raise(NotImplementedError, "Request has not been implemented in CPython Yet")
elif imp.name == 'micropython':
    if imp._machine == 'JS with Emscripten':
        _machine = imp._machine
        from pyscript import fetch

        async def f_req(self, url, method, response_type='text', body=None, startup=False):
            if body:
                data = await fetch(url, method=method, body=body)
            else:
                data = await fetch(url, method=method)
            
            if data.ok:
                if response_type == 'text':
                    state = await data.text()
                elif response_type == 'json':
                    state = await data.json()
                elif response_type == 'arrayBuffer':
                    state = await data.arraybuffer()    
                elif response_type == 'blob':
                    state = await data.blob()
                elif response_type == 'bytearray':
                    state = await data.bytearray()
            else:
                print(data.status)
                return
            
            if startup:
                self.state = state
                print('startup conplete!!\n\n\n', state)
                self.iris.on_startup('remove')
                self.send()
            else:    
                self.__call__(state)
    
    elif imp._machine == 'Evezor Edge with ESP32':
        _machine = imp._machine
        raise(NotImplementedError, "Request has not been implemented in CPython Yet")

if not f_req or not _machine:
    raise SystemError("unknown machine type")
        
class Request(Parameter):
    struct = 'j'  # json
    
    def __init__(self, url, method, response_type, on_startup, **k):
        super().__init__(**k)
        self.url = url
        self.method = method
        self.response_type = response_type
        
        if on_startup:
            print('doing request') 
            loop = asyncio.get_event_loop()
            loop.create_task(f_req(self, self.url, self.method, self.response_type, startup=True))
            self.iris.on_startup('add')

        
    