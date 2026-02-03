"""
ESP32 uart driver
"""

from Parameter import Parameter
import machine
import sys
try:
    import uasyncio as asyncio
except:
    import asyncio

class UART(Parameter):
    def __init__(self, *, bus: int, tx: int, rx: int, baud: int, encode: str, **k):
        super().__init__(**k)
        self.uart = machine.UART(bus, tx=tx, rx=rx, baudrate=baud)
        self.encode = encode  # not sure what this was for anymore
        self.buf = ''
        self.lines = []
        # self.iris.async_hw.append(self)
        
        
    def update(self):
        super().update()
        runtime = sys.implementation
        # do not run in pyscripts and other pythons
        if runtime.name == 'cpython':
            return
        if runtime._machine == 'JS with Emscripten':
            return 
        
        # self.writer = asyncio.StreamWriter(self.uart, {})
        # self.reader = asyncio.StreamReader(self.uart)

        
        loop = asyncio.get_event_loop()
        loop.create_task(self.chk())
        
    def __call__(self, msg: bytes) -> None:
        self.uart.write(msg)
        # if self.blob & 8:  # debug serial
        #     print(f'debug serial[{self.pid}]: {msg}')

    def any(self):
        if self.lines:
            return True
        return False

    def readline(self):
        return self.lines.pop(0)

    async def chk(self):
        while True:
            if self.uart.any():
                self.buf += self.uart.read().decode(self.encode)
                while True:
                    index = self.buf.find('\r\n')
                    if index == -1:
                        #empty line
                        break

                    self.lines.append(self.buf[:index])
                    self.buf = self.buf[(index + 2):]
            await asyncio.sleep_ms(0)
            
    async def xxread(self):
        while True:
            if self.lines:
                return self.lines.pop(0)
            await asyncio.sleep_ms(0)

    async def uart_receiver(self):
        """An asynchronous task to receive and process data from the UART line by line."""
        # Create a stream reader for the UART object
        
        print("UART receiver task started...")
        
        while True:
            try:
                # Asynchronously read until a newline character is found.
                # The task will yield control while it waits.
                line_bytes = await self.reader.readline()
                if line_bytes:
                    # Decode the bytes to a string and remove any trailing whitespace
                    line = line_bytes.decode('utf-8').strip()
                    print(f"Received Line: {line}")
            except asyncio.TimeoutError:
                # This is optional, but helps in debugging potential timeouts.
                print("UART read timed out.")
            except Exception as e:
                print(f"An error occurred in receiver: {e}")
                break
    
    async def uart_sender(self):
        """An asynchronous task to periodically send messages over UART."""
        # Create a stream writer for the UART object.
        
        print("UART sender task started...")
        
        counter = 0
        while True:
            message = f"Hello from MicroPython! {counter}\n"
            print(f"Sending: {message.strip()}")
            
            # Write the message bytes to the stream buffer
            self.writer.write(message.encode('utf-8'))
            
            # Asynchronously wait for the buffer to be flushed
            await self.writer.drain()
            
            counter += 1
            await asyncio.sleep(3)  # Wait for 3 seconds before sending again
    # -- async code start -------
    # def __aiter__(self):
    #     return self
    
    # async def __anext__(self):
        
    