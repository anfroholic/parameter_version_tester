# ESP32Camera

Camera Parameter for OV2640 2MP camera

**IMPORTANT:** This requires firmware compiled with camera module 

## Attributes

```python
flip: bool
mirror: bool
white_balance: str
saturation: int
brightness: int
contrast: int
quality: int
format: str
effect: str
framesize: str
```
## Methods

```python
set_flip(bool) -> None 
    # set state of flip the output along y axis

set_mirror(bool) -> None 
    # set state of camera mirroring

set_white_balance(str) -> None
    # options are the following
    NONE SUNNY CLOUDY OFFICE HOME

set_saturation(int) -> None
    "2,2 (default 0). -2 grayscale"

set_brightness(int) -> None
    "-2,2 (default 0). 2 brightness"

set_contrast(int) -> None
    "-2,2 (default 0). 2 highcontrast"

set_quality(int) -> None
    "10-63 lower number means higher quality"

set_format(int) -> None
    # options are the following
    JPEG YUV422 GRAYSCALE RGB565

set_effect(int) -> None
    # options are the following
    NONE NEG BW RED GREEN BLUE RETRO

set_framesize(int) -> None
    # options are the following
    96x96 240x240 QVGA VGA SVGA XGA HD
    SXGA UXGA P_HD P_3MP QXGA QHD WQXGA P_FHD QSXGA  

capture() -> bytearray
    # returns image from camera
```

