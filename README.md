# Pico-LuaEditorPayload
Using PICO as a payload for Seedsow Lua Editor

### Prepare

1. flash https://circuitpython.org/ with you board.
2. download it bundle and put adafruit_hid in lib folder of the board.
3. download the boot.py and code.py from my project.
4. Put the Lua file you want to load to the root folder of the board.
5. edit the code.py
TARGET_FILENAME = "file name at switch"
TARGET_SLOT     = target slot number
PAYLOAD_FILE    = "file name you put in 4."

### Usage
1. Open Seedsow Lua Editor
2. open RecievePC menu and calibrate with you joycon once.
3. Reopen Lua editor and put the Cursor at RecievePC.
3. Connect the board and wait till it blinking slowly.
4. start the RecievePC.
5. wait until it finish.
