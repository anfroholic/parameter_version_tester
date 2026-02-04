from Parameter import Parameter
from floe import make_var

class EdgeDetector(Parameter):
    
    """Operator is the parent class for things like math, logic and boolean operators"""
    def __init__(self, edge_detect: str, initial_state: bool, **k):
        super().__init__(**k)
        self.state = initial_state
        self.operator = edge_detect

    def __call__(self, state):
        if self.state != state:
            self.state = state
            if state == True and self.operator == 'rising_edge':
                super().__call__(self.state)
            if state == False and self.operator == 'falling_edge':
                super().__call__(self.state)
        
    def update(self):
        super().update()
        
    