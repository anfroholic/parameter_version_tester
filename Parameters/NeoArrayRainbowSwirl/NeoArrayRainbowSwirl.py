"""
Neopixel Rainbow Animation
"""
import math
from NeoArray import NeoArray
from floe import make_var, FP

class NeoArrayRainbowSwirl:
    """ rainbow animation for Neo"""
    rbow = tuple([int((math.sin(math.pi / 18 * i) * 127 + 128) / 10) for i in range(36)])
    
    def __init__(self, *, pid, invert, step=6, iris, **k):
        self.pid = pid
        iris.p[pid] = self
        self.iris = iris
        self.step = make_var(step)
        self.invert = make_var(invert)
        
    def __call__(self, *args, **kwargs):
        pass
    
    def animate(self, array: NeoArray, index):
        index = [(index + num * self.step.state)%36 for num in range(len(array.neos))]
        for neo, index in zip(reversed(array.neos) if self.invert.state else array.neos, index):
            color = (self.rbow[index], self.rbow[(index + 12)%36], self.rbow[(index + 24)%36])
            array.fill_strip(neo, color)

    def update(self):
        if isinstance(self.invert, FP):
            self.invert = self.iris.p[self.invert.pid]
    def gui(self):
        pass


    