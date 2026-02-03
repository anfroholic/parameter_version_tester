from Parameter import Parameter
from floe import make_var, FP
import sys, os, binascii, hashlib


class CodeBlock(Parameter):
    def __init__(self, *, code: callable, kwargs: list[FP], include_iris: bool=False, short_hash=None, **k):
        super().__init__(**k)
        self.kwargs = kwargs
        self.locals = {}
        self.filename = ""
        self.mod = None
        
        self.create_block(code, short_hash)
        
        self.func = self.mod.function
        self.state = None
        self.include_iris = include_iris
        self.blob = 1 # this is hack
        
    def __call__(self, event):
        if event is not None:
            try:
                self.state = self.func(event, *self.kwargs)
                if self.state is None:
                    return
            except Exception as e:
                print(e)
                print(sys.print_exception(e))
                self.iris.bifrost.post(e)
                return        
        self.send()
        
    
    def create_block(self, code, short_hash):
        if 'cb' not in os.listdir():
            os.mkdir('cb')
            print('creating dir')
        
        if not short_hash:
            # generate shorthash
            short_hash = hashlib.sha256(code).digest()
            short_hash = binascii.hexlify(short_hash)[:8].decode()
            print(hash)
        
        filename = f"cb{self.pid}_{short_hash}"
        if filename not in os.listdir('cb'):
            with open(f'cb/{filename}.py', 'w') as f:
                f.write(code)        
        
        self.mod = __import__(f'cb.{filename}', globals(), self.locals, ['function'])
        
    
    def update(self):
        self.kwargs = [self.iris.p[fp.pid] for fp in self.kwargs]
        if self.include_iris:
            self.kwargs.append(self.iris)
