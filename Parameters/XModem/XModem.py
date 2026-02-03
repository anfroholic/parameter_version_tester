"""
ESP32 uart driver
"""
from floe import FP, Stater, make_var
import machine
from Parameter import Parameter

try:
    import uasyncio as asyncio
except:
    import asyncio

# Control characters
SOH = 0x01  # Start of 128-byte block
STX = 0x02  # Start of 1024-byte block
EOT = 0x04  # End of Transmission
ACK = 0x06
NAK = 0x15
CAN = 0x18
C   = 0x43  # 'C' = request CRC mode

def crc16_ccitt(data):
        """Compute CRC16-CCITT"""
        crc = 0
        for byte in data:
            crc ^= (byte << 8)
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc <<= 1
            crc &= 0xFFFF
        return crc

class XModem(Parameter):
    
    def __init__(self, *, uart, block_size: str, crc_mode: bool,  **k):
        super().__init__(**k)
        self.uart = make_var(uart)
        self.block_size = int(block_size)
        self.crc_mode = crc_mode

    def __call__(self, filename: str) -> None:
        self.state = filename
        # we need to figure out a way that UART will block until we are complete
        
    async def send_file(uart, filename: str):
        block_num = 1
        use_crc = False
        block_size = 128

        # --- Wait for receiver handshake ---
        while True:
            c = uart.read(1)
            if c:
                if c[0] == NAK:
                    use_crc = False
                    block_size = 128
                    print("Receiver requested checksum mode (128 bytes)")
                    break
                elif c[0] == C:
                    use_crc = True
                    # default: CRC mode with 128 bytes
                    block_size = 128
                    print("Receiver requested CRC mode (128 bytes)")
                    break
                elif c[0] == STX:
                    # Some receivers may signal they want 1k blocks
                    use_crc = True
                    block_size = 1024
                    print("Receiver requested CRC mode (1K blocks)")
                    break

        with open(filename, "rb") as f:
            while True:
                block = f.read(block_size)
                if not block:
                    break

                # pad block to full length with 0x1A
                block = block + bytes([0x1A]) * (block_size - len(block))

                # build header
                pkt = bytearray()
                if block_size == 128:
                    pkt.append(SOH)
                else:
                    pkt.append(STX)

                pkt.append(block_num & 0xFF)
                pkt.append(0xFF - (block_num & 0xFF))
                pkt.extend(block)

                # add checksum or CRC
                if use_crc:
                    crc = crc16_ccitt(block)
                    pkt.append((crc >> 8) & 0xFF)
                    pkt.append(crc & 0xFF)
                else:
                    pkt.append(sum(block) % 256)

                # send packet and wait for ACK/NAK
                while True:
                    uart.write(pkt)
                    resp = uart.read(1)
                    if resp:
                        if resp[0] == ACK:
                            block_num = (block_num + 1) % 256
                            break
                        elif resp[0] == NAK:
                            print("NAK received, resending block", block_num)
                            continue
                        elif resp[0] == CAN:
                            print("Transfer canceled by receiver")
                            return False

            # --- End transmission ---
            while True:
                uart.write(bytes([EOT]))
                resp = uart.read(1)
                if resp and resp[0] == ACK:
                    break

        print("Transfer complete")
        return True




    async def chk(self):
        while True:
            if self.uart.any():
                self.buf += self.uart.read().decode(self.encode)
                while True:
                    index = self.buf.find('\r\n')
                    if index == -1:
                        break

                    self.lines.append(self.buf[:index])
                    self.buf = self.buf[(index + 2):]
            await asyncio.sleep_ms(0)
            
