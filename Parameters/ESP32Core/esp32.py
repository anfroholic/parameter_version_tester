# fake module for pyscripts

class CAN:
    NORMAL = None
    LOOPBACK = None
    SILENT = None
    def __init__(self, *args, **kwargs):
        pass
    def send(self, *args, **kwargs):
        pass
    def any(self):
        return False
