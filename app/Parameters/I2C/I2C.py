"""
ESP32 i2c driver    
"""

from Parameter import Parameter, Iris
import floe
try:
    import machine
except:
    import fakes.machine as machine

class I2C: 
    def __init__(self, *, sda:int, scl:int, bus:int, baud:int, pid: int, iris: Iris, **k):
        self.i2c = machine.I2C(bus, scl=machine.Pin(scl), sda=machine.Pin(sda), freq=baud)
        iris.p[pid] = self
        self.devices = self.i2c.scan()
        
    def update(self):
        pass
    
    def gui(self):
        return None
    
    def verify_address(self, address):
        if address in self.devices:
            print(f'device at {address} found')
            return True
        
        print('TODO: Make Error Handling')
        return False
    