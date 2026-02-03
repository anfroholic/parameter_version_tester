from Parameter import Parameter
from floe import make_var

class Operator(Parameter):
    operators = {
                    "add": "+",
                    "subtract": "-",
                    "divide": "/",
                    "floor_divide": "//",
                    "modulo": "%",
                    "power": "**",
                    "root": "root",
                    "equal_to": "==",
                    "not_equal_to": "!=",
                    "greater_than": ">",
                    "less_than": "<",
                    "NOT": "~",
                    "AND": "&",
                    "OR": "|",
                    "XOR": "^",
                    "right_shift": ">>",
                    "left_shift": "<<"
                }
    """Operator is the parent class for things like math, logic and boolean operators"""
    def __init__(self, *, input1, input2, operator_type: str, **k):
        super().__init__(**k)
        self.input1 = make_var(input1)
        self.input2 = make_var(input2)
        self.state = 0
        self.operator = self.operators[operator_type]

    def __call__(self, state):
        '''state is ignored and whole expression is evaluated'''
        self.state = self.do_op()
        super().__call__(self.state)
        
    def update(self):
        super().update()
        if not self.input1.state or not self.input2.state:
            raise ValueError(f'Operator with pid: {self.pid} requires two inputs')
        self.input1.add_hot(self)
        self.input2.add_hot(self)    
        self.state = self.do_op()
        
    def do_op(self):
        if self.operator == 'root':
            return eval(f"{self.input1.state} ** (1/{self.input2.state})")
        return eval(f"{self.input1.state} {self.operator} {self.input2.state}")
    