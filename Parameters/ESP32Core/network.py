# fake objects for pyscript

class WLAN:
    def __init__(self, *args, **kwargs):
        pass
    
    def config(self, *args, **kwargs):
        pass
    
    def active(self, *args, **kwargs):
        pass
    
    def isconnected(self, *args, **kwargs):
        return True