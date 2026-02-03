"""
Neopixel Rainbow Animation
"""
import math
from NeoArray import NeoArray

class NeoArrayRainbow:
    """ rainbow animation for Neo
    """
    rbow = tuple([int((math.sin(math.pi / 18 * i) * 127 + 128) / 10) for i in range(36)])
    
    def __init__(self, *, pid, iris, **k):
        self.pid = int(pid)
        iris.p[pid] = self
        
    def __call__(self, *args, **kwargs):
        pass
    
    def animate(self, array: NeoArray, index):
        index %= 36
        color = (self.rbow[index], self.rbow[(index + 12)%36], self.rbow[(index + 24)%36])
        array.fill(color)
       
    def update(self):
        pass
    
    def gui(self):
        pass

    