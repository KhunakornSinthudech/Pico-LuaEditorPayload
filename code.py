import time
import struct
import board
import digitalio
import usb_hid

# ================= File and Target Configuration =================
TARGET_FILENAME = "core.lua"
TARGET_SLOT     = None
PAYLOAD_FILE    = "core_compact.lua"

PREPARE_TIME = 0.02
HOLD_TIME    = 0.035

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

pads = [d for d in usb_hid.devices if d.usage_page == 0x01 and d.usage == 0x05]
pad = pads[0] if pads else None

HORI_Y = 0x01
HORI_B = 0x02
HORI_A = 0x04
HORI_X = 0x08
HORI_L = 0x10
HORI_R = 0x20

NEUTRAL = bytes([0x00, 0x00, 0x08, 0x80, 0x80, 0x80, 0x80, 0x00])

def send_pad(b0=0x00):
    if pad:
        pad.send_report(bytes([b0, 0x00, 0x08, 0x80, 0x80, 0x80, 0x80, 0x00]))

def adler32(data):
    a = 1
    b = 0
    for byte in data:
        a = (a + byte) % 65521
        b = (b + a) % 65521
    return (b << 16) | a

def destination(slot=None):
    if slot is None:
        return "F000"
    if not (4 <= slot <= 120):
        raise ValueError("Slot must be between 4 and 120")
    return "P{:03d}".format(slot)

def pack_sse2(name, source):
    if isinstance(source, str):
        source = source.encode("utf-8")
    encoded_name = name.encode("ascii")
    checksum = adler32(source)
    header = b"SSE2\x01" + struct.pack("<II", len(source), checksum) + bytes([len(encoded_name)])
    return header + encoded_name + source

def symbols(packet):
    for byte in packet:
        yield (byte >> 4) & 0x0F
        yield byte & 0x0F

def nibble_to_hori_mask(nibble):
    mask = 0x00
    if nibble & 1: mask |= HORI_A
    if nibble & 2: mask |= HORI_B
    if nibble & 4: mask |= HORI_X
    if nibble & 8: mask |= HORI_Y
    return mask

def transmit_packet(packet, prepare=PREPARE_TIME, hold=HOLD_TIME):
    clock = False
    send_pad(0x00)
    time.sleep(1.0)

    for nibble in symbols(packet):
        face_mask = nibble_to_hori_mask(nibble)

        b0_prep = face_mask | (HORI_R if clock else 0x00)
        send_pad(b0_prep)
        time.sleep(prepare)

        clock = not clock
        b0_hold = face_mask | (HORI_R if clock else 0x00)
        send_pad(b0_hold)
        led.value = clock
        time.sleep(hold)

    send_pad(0x00)
    led.value = False
    time.sleep(0.5)

time.sleep(3.0)

for _ in range(3):
    send_pad(HORI_L)
    time.sleep(0.25)
    send_pad(0x00)
    time.sleep(0.25)

for _ in range(10):
    led.value = True
    time.sleep(0.5)
    led.value = False
    time.sleep(0.5)

send_pad(0x00)
time.sleep(1.0)

try:
    with open(PAYLOAD_FILE, "rb") as f:
        source_bytes = f.read()
except OSError:
    source_bytes = b'print("Hello from Pico 2 W SSE2!")\n'

mode_prefix = destination(TARGET_SLOT)
full_name = "{}_{}".format(mode_prefix, TARGET_FILENAME)
packet = pack_sse2(full_name, source_bytes)

transmit_packet(packet)

for _ in range(20):
    led.value = not led.value
    time.sleep(0.1)
led.value = False