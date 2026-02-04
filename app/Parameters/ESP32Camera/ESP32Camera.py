"""
ESP32 Camera OV2640
"""

from floe import FP, make_var
from Parameter import Parameter

import machine, gc

try:
    import uasyncio as asyncio
except:
    import asyncio    
import camera


framesizes = {
          "96x96": camera.FRAME_96X96,
          "240x240": camera.FRAME_240X240,
          "QVGA": camera.FRAME_QVGA,
          "VGA": camera.FRAME_VGA,
          "SVGA": camera.FRAME_SVGA,
          "XGA": camera.FRAME_XGA,
          "HD": camera.FRAME_HD,
          "SXGA": camera.FRAME_SXGA,
          "UXGA": camera.FRAME_UXGA,
          "P_HD": camera.FRAME_P_HD,
          "P_3MP": camera.FRAME_P_3MP,
          "QXGA": camera.FRAME_QXGA,
          "QHD": camera.FRAME_QHD,
          "WQXGA": camera.FRAME_WQXGA,
          "P_FHD": camera.FRAME_P_FHD,
          "QSXGA": camera.FRAME_QSXGA
        }

frequencies = {
          "10MHz": camera.XCLK_10MHz,
          "20MHz": camera.XCLK_20MHz
        }

white_balances = {
          "NONE": camera.WB_NONE,
          "SUNNY": camera.WB_SUNNY,
          "CLOUDY": camera.WB_CLOUDY,
          "OFFICE": camera.WB_OFFICE,
          "HOME": camera.WB_HOME
        }

effects = {
          "NONE": camera.EFFECT_NONE,
          "NEG": camera.EFFECT_NEG,
          "BW": camera.EFFECT_BW,
          "RED": camera.EFFECT_RED,
          "GREEN": camera.EFFECT_GREEN,
          "BLUE": camera.EFFECT_BLUE,
          "RETRO": camera.EFFECT_RETRO
        }

formats = {
          "JPEG": camera.JPEG,
          "YUV422": camera.YUV422,
          "GRAYSCALE": camera.GRAYSCALE,
          "RGB565": camera.RGB565
        }

fb_locations = {
          "PSRAM": camera.PSRAM
        }

class ESP32Camera(Parameter):
    struct = 'f'  # float
    
    def __init__(self, 
                 flip: bool,
                 mirror: bool,
                 white_balance: str,
                 saturation: int,
                 brightness: int,
                 contrast: int,
                 quality: int,                 
                 format: str,
                 effect: str,
                 framesize: str,  
                 clk_frequency: str,
                 d0_pin: int,
                 d1_pin: int,
                 d2_pin: int,
                 d3_pin: int,
                 d4_pin: int,
                 d5_pin: int,
                 d6_pin: int,
                 d7_pin: int,
                 href_pin: int,
                 vsync_pin: int,
                 sioc_pin: int,
                 siod_pin: int,
                 xclk_pin: int,
                 pclk_pin: int,
                 fb_location: str,                 
                 **k):
        super().__init__(**k)

        self.flip = flip
        self.mirror = mirror
        self.white_balance = white_balance
        self.saturation = saturation
        self.brightness = brightness
        self.contrast = contrast
        self.quality = quality
        self.effect = effect
        
        # Disable camera initialization
        camera.deinit()
        # Enable camera initialization
        camera.init(0, 
                    d0=d0_pin, 
                    d1=d1_pin, 
                    d2=d2_pin, 
                    d3=d3_pin, 
                    d4=d4_pin, 
                    d5=d5_pin, 
                    d6=d6_pin, 
                    d7=d7_pin,
                    href=href_pin, 
                    vsync=vsync_pin, 
                    reset=-1, 
                    pwdn=-1,
                    sioc=sioc_pin, 
                    siod=siod_pin, 
                    xclk=xclk_pin, 
                    pclk=pclk_pin, 
                    format=formats[format], 
                    framesize=framesizes[framesize], 
                    xclk_freq=frequencies[clk_frequency],
                    fb_location=fb_locations[fb_location])
        
        self.set_flip(flip)
        self.set_mirror(mirror)
        self.set_saturation(saturation)
        self.set_brightness(brightness)
        self.set_contrast(contrast)
        self.set_quality(quality)
        self.set_effect(effect)
        self.set_white_balance(white_balance)
    
    def set_flip(self, flip: bool):
        self.flip = flip
        camera.flip(int(flip))

    def set_mirror(self, mirror: bool):
        self.mirror = mirror
        camera.mirror(int(mirror))

    def set_white_balance(self, white_balance: str):
        self.white_balance = white_balance
        camera.whitebalance(white_balances[white_balance])
    
    def set_saturation(self, saturation: int):
        self.saturation = saturation
        camera.saturation(saturation)
        
    def set_brightness(self, brightness: int):
        self.brightness = brightness
        camera.brightness(brightness)
    
    def set_contrast(self, contrast: int):
        self.contrast = contrast
        camera.contrast(contrast)
    
    def set_quality(self, quality: int):
        self.quality = quality
        camera.quality(quality)
    
    def set_effect(self, effect: str):
        self.effect = effect
        camera.speffect(effects[effect])
   
    def set_framesize(self, framesize: str):
        self.framesize = framesize
        camera.framesize(framesizes[framesize])
    
    def set_format(self, format: str):
        self.format = format
        camera.format(formats[format])
        
    def capture(self):
        gc.collect()
        return camera.capture()
    
    def setup_picoweb(self, start_response):
        return [("/video", self._video(start_response))]

    def _video(self, start_response):
        # Video transmission
        def send_frame():
            buf = camera.capture()
            yield (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n'
            + buf + b'\r\n')
            del buf
            gc.collect()
        
        def video(req, resp):
            yield from start_response(resp, content_type="multipart/x-mixed-replace; boundary=frame")
            while True:
                yield from resp.awrite(next(send_frame()))
        return video
     
    
    

