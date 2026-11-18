# Pico-LuaEditorPayload
Use a Raspberry Pi Pico as a payload sender for the Seedsow Lua Editor.

The Pico identifies itself as a HORI wired gamepad (VID `0x0F0D`, PID `0x0092`)
and sends a Lua file by pressing buttons: each 4-bit nibble is encoded on
A/B/X/Y, and every nibble is latched by toggling R. The packet carries a
header with the target name, length and an Adler-32 checksum.

### Prepare

1. Flash [CircuitPython](https://circuitpython.org/) onto your board.
2. Download the CircuitPython library bundle and copy `adafruit_hid` into the board's `lib` folder.
3. Download `boot.py` and `code.py` from this project.
4. Copy the Lua file you want to send to the root folder of the board.
5. Edit the settings at the top of `code.py`:
   ```python
   TARGET_FILENAME = "core.lua"          # file name on the Switch side
   TARGET_SLOT     = None                # None -> F000_<name>, 4..120 -> P###_<name>
   PAYLOAD_FILE    = "core_compact.lua"  # the file you copied in step 4
   START_BUTTON_PIN = None               # optional, e.g. board.GP14 (see below)
   ```
6. Copy `boot.py` and `code.py` to the root folder of the board.

### Editing files on the board later

Once `boot.py` is installed, the board no longer shows up as a USB drive.
To get the drive back, **short GP15 to GND** and plug the board in. In this
mode the board does nothing else and is safe to edit.

### Usage
1. Open the Seedsow Lua Editor.
2. Open the `RecievePC` menu and calibrate with your Joy-Con once.
3. Reopen the Lua editor and put the cursor on `RecievePC`.
4. Connect the board and wait until it blinks slowly.
5. Start `RecievePC`.
   - Without a start button you have about 10 seconds of slow blinking.
   - With `START_BUTTON_PIN` set, it keeps blinking until you press the button.
6. Wait until it finishes (fast blinking for 2 seconds at the end).

### LED patterns

| Pattern | Meaning |
|---|---|
| Slow blink (0.5 s) | Waiting for you to start `RecievePC` |
| Flicker | Sending |
| Fast blink for 2 s, then off | Done |
| Fast blink that never stops | Error, nothing was sent (payload file missing or empty, bad `TARGET_SLOT`, or no gamepad device) |
| Solid on | GP15 is shorted: file-edit mode |
