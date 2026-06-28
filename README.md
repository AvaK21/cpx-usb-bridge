# cpx-usb-bridge

A minimal serial protocol for sending state-change commands from a PC to an Adafruit Circuit Playground Express (CPX) over USB, using a dedicated `usb_cdc.data` channel (not the REPL console).

The CPX receives a command (`idle`, `alert`, `cool`), updates its onboard NeoPixels, and writes a confirmation back to the PC. Built as a foundation for piping computer-vision output into physical state changes on the board.

## Why this isn't just `print()`/`input()`

CircuitPython's console serial (the one Mu/Tera Term connect to) echoes every byte it receives — it's built for interactive REPL use, not machine-to-machine messaging. Using it for a data protocol causes garbled, inconsistent responses (commands get mixed with their own echo).

This project enables a **second, dedicated USB CDC interface** (`usb_cdc.data`) via `boot.py`, so protocol traffic and human-readable debug output never share a channel.

## Repo structure

```
cpx-usb-bridge/
├── cpx/
│   └── code.py         # Runs on the CPX board
|   └── boot.py         # Enables the dual USB CDC interface — goes on 
├── pc/
│   └── pc_usb.py       # Runs on the PC
CIRCUITPY root
└── README.md
└── requirements.txt
```

## Setup

### 1. Flash the CPX side

Copy these two files to the **root** of the CIRCUITPY drive:
- `boot.py`
- `cpx/code.py` → rename to `code.py` on the drive (CircuitPython requires this exact filename to auto-run)

### 2. Reboot the board — this step is easy to miss

`boot.py` only runs on an actual power cycle, **not** on save/auto-reload like `code.py` does.

**Physically unplug and replug the CPX from USB.**

### 3. Verify two COM ports exist

After reboot, check Device Manager (Windows) or `ls /dev/tty.*` / `ls /dev/ttyACM*` (Mac/Linux). You should see **two** CPX serial ports now instead of one:
- **Console** — the original REPL/debug port (what Mu's serial console connects to)
- **Data** — the new port this project's PC script actually talks to

Windows won't label which is which. To find out:
- Open Mu's serial console on one of the two ports. If you see the CircuitPython REPL prompt, that one is console — the other is data.
- Or check which port shows a *new* driver install timestamp in Device Manager right after the reboot in step 2 — that's the freshly-created data interface.

### 4. Run the PC script

```bash
pip install pyserial
```

In `pc/pc_usb.py`, set `COM_PORT` to the **data** port identified in step 3, then run:

```bash
python pc/pc_usb.py
```

Enter `idle`, `alert`, or `cool` at the prompt. The CPX's NeoPixels should change color, and the script should print a matching confirmation, e.g. `CPX Response: State: cool`.

## Protocol

- Commands are plain ASCII strings terminated with `\n`.
- Valid commands: `idle`, `alert`, `cool`.
- CPX responds with `State: <command>\n` on success, or `Unknown command: <text>\n` if the command isn't recognized.
- Any unhandled runtime error on the CPX side is caught and reported back as `Error: <message>\n` rather than crashing the board.

## Known limitations / not yet handled

- No reconnect logic if the CPX is unplugged mid-session — the PC script will raise `SerialException` and exit.
- COM/tty port identification is manual (see step 3). Auto-detection by VID:PID alone isn't sufficient since both the console and data interfaces share the same hardware ID — they're only distinguishable by behavior.
- Single-word commands only; no support yet for structured/multi-field messages.

## Hardware

- [Adafruit Circuit Playground Express](https://www.adafruit.com/product/3333)
- Tested with CircuitPython 10.x
