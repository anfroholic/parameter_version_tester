from Parameter import Parameter
from floe import Bifrost
from iris import Iris
import os, sys, json, gc, struct
import network
import time
import machine
import binascii
from FileReceiver import FileReceiver

default_env = '{"ap_mode": false, "station_mode": false, "wifi_ssid": null, "wifi_password": null}'

NEO_STATUS = {
    "connecting": {   # blue-lightblue
        "colors": (b'\x00\x01\x03', b'\x00\x00\x07'),
        "delay": 500,
    },
    "unconnected": {  # fast amber-white
        "colors": (b'\x05\x03\x00', b'\x02\x02\x02'),
        "delay": 200,   
    },
    "error": {        # fast red-amber
        "colors": (b'\x13\x00\x00', b'\x05\x05\x00'),
        "delay": 300,
    },
    "fatal_error": {  # slow red blink
        "colors": (b'\x13\x00\x00', b'\x00\x00\x00'),
        "delay": 700,
    },
}

def getblobs(iris):
    gc.collect()
    blobs = [b'myblobs']
    for pid, param in iris.p.items():
        if hasattr(param, 'blob'):
            blob = struct.pack('H', pid)
            blob += struct.pack("B", param.blob)
            blobs.append(blob)
    blobmap = b''.join(blobs)    
    return blobmap

# These are subscriptions to nwk channel
def esp32_narrowband(msg, iris):
    if msg == b'reset':
        machine.reset()
    elif msg == b'lghtshw':
        iris.core.neo_status.lightshow()
    elif msg == b'getblobs':
        iris.bus.debug(f"{getblobs(iris)}")

class ESP32Core(Parameter):
    def __init__(self, *, 
                 pid, 
                 name,
                 bus, 
                 function_button, 
                 neo_status, 
                 hbt_led, 
                 terminal:bool=False, 
                 wifi,
                 webserver, 
                 iris, 
                 **k):
        super().__init__(pid=pid, iris=iris, **k)
        self.name = name
        self.bus = bus
        self.webserver = webserver
        self.terminal = terminal
        self.function_button = function_button
        if neo_status:
            self.neo_status = neo_status
        else:
            self.neo_status = lambda x: x
        self.hbt_led = hbt_led
        self.wifi = wifi
        
        self.wlan = None
        self.iris: Iris = iris
        iris.core = self
        
        iris.id = binascii.b2a_base64(machine.unique_id(), False)
        iris.n[500] = (esp32_narrowband)
        # add standard components
        
    def boot(self):
        runtime = sys.implementation
        # do not run async in pyscripts and other pythons
        if runtime.name == 'cpython':
            return
        if runtime._machine == 'JS with Emscripten':
            return 
        fs = FileReceiver(name="no_name", pid=65500, debug=False, active=True, bcast=True, iris=self.iris)
        fs.update()
        
        if '.env' not in os.listdir():
            with open('.env', 'w') as f:
                f.write(default_env)
        
        with open('.env', 'r') as f:
                env = json.load(f)
        
        self.neo_status(b'\x02\x00\x00') # red
        if self.wifi:            
            if env['ap_mode'] is True:
                print('starting wifi in ap mode')
                self.setup_wifi_ap(ssid=env['wifi_ssid'], password=env['wifi_password'])
                self.neo_status(b'\x02\x04\x00') # amber
            if env['station_mode'] is True:
                print('connecting wifi to station')
                self.connect_to_wifi_station(env['wifi_ssid'], env['wifi_password'])
                self.neo_status(b'\x00\x04\x01')  # green
            else:
                print('starting wifi to to ap setup mode')
                self.setup_wifi_ap()
                self.neo_status(b'\x02\x04\x00')  # yellow
            print(f'http://{self.wlan.ifconfig()[0]}')
            

        else:
            self.neo_status(b'\x00\x00\x00')  # off
        
        if self.webserver:
            self.webserver.boot()
    
    def setup_wifi_ap(self, *, ssid=None, password=None):
        self.wlan = network.WLAN(network.AP_IF)
        if ssid:
            try:
                if password:
                    self.wlan.config(essid=ssid, password=password)
                else:
                    self.wlan.config(essid=ssid)
            except OSError:
                print('Wifi Internal Error\nresetting...\n*******\n')
                machine.reset()
        else:
            self.wlan.config(essid='evezor_setup')
        # self.wlan.config(max_clients=1)
        self.wlan.active(True)
                    
    def connect_to_wifi_station(self, ssid, password):
        self.wlan =  network.WLAN(network.STA_IF)
        self.wlan.active(True)
        if not self.wlan.isconnected():
            print('connecting to network...')
            try:
                self.wlan.connect(ssid, password)
            except OSError:
                print('Wifi Internal Error\nresetting...\n*******\n')
                self.neo_status.off()
                machine.reset()
        neo_state = 0
        color = NEO_STATUS['connecting']['colors']
        while not self.wlan.isconnected():
            if neo_state % 2:
                self.neo_status(color[0])
            else:
                self.neo_status(color[1])
            time.sleep(.5)
            neo_state += 1
            print('.', end='')
        print('connected')
    
    @staticmethod
    def reset():
        "reset environment variables"
        with open('.env', 'w') as f:
            f.write(default_env)

    def set_error(self, error):
        self.neo_status.start_blinker(**NEO_STATUS[error])



