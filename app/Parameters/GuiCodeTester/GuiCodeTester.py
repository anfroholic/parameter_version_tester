from Parameter import Parameter

from floe import make_var, implementation
import sys, io, json

class GuiCodeTester(Parameter):
    struct = 'e'  # bool
    
    def __init__(self, *, code, description, buttons, name: str = "", initial_value:str = "", iris, **k):
        super().__init__(name=name, iris=iris, **k)
        self.name = name
        self.state = initial_value
        self.code = make_var(code)
        self.buttons = make_var(buttons)
        self.description = make_var(description)
        self.locals = {"iris": iris}
        self.implementation = implementation.name
        
    
    def __call__(self, state, gui=False):
        #super().__call__(state)
        state = json.loads(state)
        cmd = state['cmd']
        if cmd == 'term':
            # globals()['post'] = self.post
            # globals().update(self.locals)
            result = self.do_repl(state['msg'])
            self.post(result)
        elif cmd == 'button':
            code = self.buttons.state[state['msg']]
            self.post(f">>> {code}")
            # globals()['post'] = self.post
            # globals().update(self.locals)
            result = self.do_repl(code)
            if result != "None":
                self.post(result)

        if not gui:
            self.iris.bifrost.send(self.pid, self.state)

    def update(self):
        super().update()
        code = self.code.state.replace('\t', '    ')
        self.do_repl(code)
        self.locals['post'] = self.post 
        # globals().update(self.locals)
        
        # self.locals['post'] = lambda msg: self.iris.bifrost.send(self.pid, {"cmd": "term", "msg": msg})

        
    def gui(self):
        return {"name": self.name, "pid": self.pid, "state": self.state, "code": self.code.state, "description": self.description.state, "buttons": self.buttons.state, "type": "GuiCodeTester"}
    
    def post(self, msg):
        print(self.name)
        self.iris.bifrost.send(self.pid, {"cmd": "term", "msg": msg})
    
    def do_repl(self, code: str):
        # print('repling', code)
        code.replace('<br>', '\n')
        code.replace('&nbsp;', ' ')
        # print(code)
        try:
            
            _return = str(eval(code, self.locals, self.locals))
            return _return

        except SyntaxError:
            try:
                exec(compile(code, 'input', 'exec'), self.locals, self.locals)
                return "<empty string>"
            except Exception as e:
                if self.implementation == 'cpython':
                    return f">>> {code}\nexception: {repr(e)}"
                thing = io.StringIO()
                sys.print_exception(e, thing)
                print(thing.getvalue())
                return f">>> {code}\nexception: {thing.getvalue()}"

        except Exception as e:
            if self.implementation == 'cpython':
                return f">>> {code}\nexception: {repr(e)}"
            thing = io.StringIO()
            sys.print_exception(e, thing)
            print(thing.getvalue())
            return f">>> {code}\nexception: {thing.getvalue()}"

