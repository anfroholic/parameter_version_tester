# fake objects for pyscript

def unique_id():
    return b"py_ESP32"

def reset():
    pass
def soft_reset():
    pass
def freq(*arg):
    pass


class Pin:
    OUT = None
    IN = None
    PULL_DOWN = None
    PULL_UP = None
    IRQ_FALLING = None
    IRQ_RISING = None
    def __init__(self, *args, **kwargs):
        pass    
        
    def on(self):
        pass
    
    def off(self):
        pass
    
    def low(self):
        pass
    
    def high(self):
        pass
    
    def value(self, *args, **kwargs):
        return False
    def irq(self, *args, **kwargs):
        pass
      
class ADC:
    ATTN_0DB = 9
    ATTN_2_5DB = 10
    ATTN_6DB = 11
    ATTN_11DB = 12
    def __init__(self, *args, **kwargs):
        pass
    
    def read_uv(self):
        return 0
    def read_u16(self):
        return 0
    def read(self):
        return 0
    def atten(self, *args):
        pass
    def width(self, *args):
        pass

class I2C:
    def __init__(self, *args, **kwargs):
        pass
    
    def scan(self):
        return [i for i in range(127)]
    def readfrom(self, *args):
        return 0
    def writeto(self, *args):
        pass
    def readfrom_mem(self, *args):
        return 0
    def writeto_mem(self, *args):
        pass
    def readfrom_into(self, *args):
        pass
    def writeto(self, *args):
        pass
    def writevto(self, *args):
        pass
    
class UART:
    def __init__(self, *args, **kwargs):
        pass
    
    def any(self):
        return False
    def read(self, *args):
        return None
    def write(self, *args):
        return None
    def readinto(self, *args):
        return None
    def readline(self, *args):
        return ""

class PWM:
    def __init__(self, *args, **kwargs):
        pass
    def init(self, *arg, **kwargs):
        pass
    def freq(*args):
        return None
    def duty(*args): 
        return None
    def duty_u16(*args): 
        return None
    def duty__ns(*args): 
        return None
    def deinit():
        pass
    
class SDCard:
    def __init__(self, *args, **kwargs):
        pass

class Timer:
    PERIODIC = None
    ONE_SHOT = None
    def __init__(self, *args, **kwargs):
        pass
    def init(self, *args, **kwargs):
        pass