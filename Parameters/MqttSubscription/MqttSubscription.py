from Parameter import Parameter
from floe import make_var
import json



class MqttSubscription(Parameter):
    
    """Operator is the parent class for things like math, logic and boolean operators"""
    def __init__(self, *, topic: str, convert_to_type, iris, **k):
        super().__init__(iris=iris, **k)
        self.topic = topic
        self.ct = self.set_ct(convert_to_type)
    
    def update(self):
        super().update()
         
        for param in self.iris.p.values():
            # find the mqtt bus and add subscription
            if param.__class__.__name__ in ('MqttBus', 'UMqttBus'):
                param.special_subscribe(self.topic, self)

    def __call__(self, state):
        try:
            state = self.ct(state)
        except:
            self.iris.post('make an exception for MqttSubscription')
        super.__call__(state)
            
    def set_ct(self, ct):
        converts = {
            'bytes': lambda m: m,
            'string': lambda m: m.decode(),
            'int': lambda m: int(m),
            'float': lambda m: float(m),
            'json': lambda m: json.loads(m.decode()),
        }
        self.ct = converts[ct]
        
        
        
        
        
        
    