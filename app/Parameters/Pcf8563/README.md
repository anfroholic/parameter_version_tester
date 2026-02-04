# Pcf8563

The Pcf8563 Parameter is used to interface with the pcf8563 Real Time Clock Module

- Provides year, month, day, weekday, hours, minutes, and seconds based on a 32.768 kHz quartz crystal
- Century flag
- Clock operating voltage: 1.0 V to 5.5 V at room temperature
- Low backup current; typical 0.25 uA at VDD = 3.0 V and T amb = 25C
- 400 kHz two-wire I 2C-bus interface (at VDD = 1.8 V to 5.5 V)
- Programmable clock output for peripheral devices (32.768 kHz, 1.024 kHz, 32 Hz, and 1 Hz)
- Alarm and timer functions
- Integrated oscillator capacitor
- Internal Power-On Reset (POR)
- I2C-bus slave address: read A3h and write A2h
- Open-drain interrupt pin