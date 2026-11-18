import time
import struct
import board
import digitalio
import usb_hid

# ================= File and Target Configuration =================
TARGET_FILENAME = "core.lua"
TARGET_SLOT     = None              # None -> F000_<name>, 4..120 -> P###_<name>
PAYLOAD_FILE    = "core_compact.lua"

# Timing per nibble (seconds). If transfers fail the checksum, raise these
# first: PREPARE_TIME should be at least one frame of the receiving app.
PREPARE_TIME = 0.02
HOLD_TIME    = 0.035

# Optional start button: wire a push button between this pin and GND,
# e.g. START_BUTTON_PIN = board.GP14. With None, the board waits a fixed
# 10 seconds (slow blink) before sending, as before.
START_BUTTON_PIN = None

# Same pin boot.py checks. Shorted to GND = file-edit mode, no gamepad.
MAINTENANCE_PIN = board.GP15

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT


def halt_with_error():
    # Fast blink forever: something is wrong, nothing was sent.
    while True:
        led.value = not led.value
        time.sleep(0.08)


# ---- File-edit mode: do nothing so the drive can be edited safely ----
maint = digitalio.DigitalInOut(MAINTENANCE_PIN)
maint.switch_to_input(pull=digitalio.Pull.UP)
if not maint.value:
    print("GP15 shorted: file-edit mode, not sending.")
    led.value = True
    raise SystemExit
maint.deinit()

pads = [d for d in usb_hid.devices if d.usage_page == 0x01 and d.usage == 0x05]
if not pads:
    halt_with_error()
pad = pads[0]

HORI_Y = 0x01
HORI_B = 0x02
HORI_A = 0x04
HORI_X = 0x08
HORI_L = 0x10
HORI_R = 0x20


def send_pad(b0=0x00):
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
    if len(encoded_name) > 255:
        raise ValueError("Target name too long")
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


# ---- Build the packet BEFORE touching the console, so a bad config
# ---- never sends anything (and never overwrites the target file).
try:
    with open(PAYLOAD_FILE, "rb") as f:
        source_bytes = f.read()
except OSError:
    print("Payload file not found:", PAYLOAD_FILE)
    halt_with_error()

if not source_bytes:
    print("Payload file is empty:", PAYLOAD_FILE)
    halt_with_error()

try:
    full_name = "{}_{}".format(destination(TARGET_SLOT), TARGET_FILENAME)
    packet = pack_sse2(full_name, source_bytes)
except ValueError as e:
    print("Config error:", e)
    halt_with_error()


# ---- Handshake with the console ----
time.sleep(3.0)

for _ in range(3):
    send_pad(HORI_L)
    time.sleep(0.25)
    send_pad(0x00)
    time.sleep(0.25)

if START_BUTTON_PIN is not None:
    btn = digitalio.DigitalInOut(START_BUTTON_PIN)
    btn.switch_to_input(pull=digitalio.Pull.UP)
    # Slow blink until the button is pressed (start RecievePC, then press).
    last = time.monotonic()
    while btn.value:
        if time.monotonic() - last >= 0.5:
            led.value = not led.value
            last = time.monotonic()
        time.sleep(0.01)
    led.value = False
    time.sleep(0.5)
else:
    for _ in range(10):
        led.value = True
        time.sleep(0.5)
        led.value = False
        time.sleep(0.5)

send_pad(0x00)
time.sleep(1.0)

transmit_packet(packet)

for _ in range(20):
    led.value = not led.value
    time.sleep(0.1)
led.value = False
