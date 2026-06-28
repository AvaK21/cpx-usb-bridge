"""CPX USB Read Example and chagne LEDs state based on USB read value.
This code will be run on the Circuit Playground Express (CPX) board. It will read data from the USB serial input and change the state of the onboard LED based on the received value.
Plan: it be via state machine"""

#Name needs to changed to code.py to run on the CPX board.

import time
from adafruit_circuitplayground import cp
import usb_cdc

serial = usb_cdc.data  # Use the data USB CDC interface for communication
buf = b""  # Buffer to hold incoming data


class State:
    """Enum-like class to represent different states. Not using the enum module to keep it simple for CircuitPython. And decrease RAM usage."""
    IDLE = "idle"
    ALERT = "alert"
    COOL = "cool"





def apply_state(state):
    """Apply the given state to the CPX board."""
    if state == State.IDLE:
        cp.pixels.fill((0, 0, 200))  
    elif state == State.ALERT:
        cp.pixels.fill((200, 0, 0))
    elif state == State.COOL:
        cp.pixels.fill((0, 200, 0))


def read_usb():
    """Line read from USB serial."""
    global buf
    #IF there are bytes waiting in the buffer
    if serial.in_waiting:
        #Read the number of bytes waiting and add them to the buffer
        buf += serial.read(serial.in_waiting)
        #Check if we have a complete line (ending with newline character)
        if  b'\n' in buf:
            # line,seperator, buf = buf.partition(b'\n')  # Split of before seperator, seperator, and after seperator.
            # Buf us updated to contain the remaining data after the '\n'
            line, _, buf = buf.partition(b'\n')     
            line = line.decode().strip()
            return line
        else:
            return None
    else: 
        return None

"""Initialize the CPX board to the default state."""
cp.pixels.brightness = 0.01  # Set brightness to a reasonable level
curent_state = State.IDLE
apply_state(curent_state)


"""Main loop to read commands from USB and change the state of the CPX board accordingly."""
while True:
    try:
        cmd = read_usb()
        if cmd is not None:
            if cmd in (State.IDLE, State.ALERT, State.COOL):
                curent_state = cmd
                apply_state(curent_state)
                serial.write(f"State: {curent_state}\n".encode())
                #print(f"State changed to: {curent_state}")
            else:
                serial.write(f"Unknown command: {cmd}\n".encode())
    except Exception as e:
        serial.write(f"Error: {str(e)}\n".encode())
    time.sleep(0.05)  # Small delay to avoid busy waiting
