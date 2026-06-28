"""Basic Code for PC to send/receive data to/from the CPX via USB"""
#This code will be run in a different environment, on a PC to handle dependencies.
import time
import serial



def read_response(ser):
    """Read a line from the serial port. With a timeout of 2 seconds."""
    start = time.time()
    response = ""
    while time.time() - start <2: 
        line = ser.readline().decode().strip()
        if line:
            response = line
            break
    if response:
        print(f"CPX Response: {response}")
    else:
        print("No CPX response")


def main():
    """Main function to send commands to the CPX via USB serial."""
    COM_PORT = "COM3"
    BAUD_RATE = 115200

    try:
        ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
    except serial.SerialException as e:
        print(f"Error opening serial port {COM_PORT}: {e}")
        return

    time.sleep(2)  # Wait for the serial connection to initialize
    #CPX expects a newline character at the end of the command, so we include '\n' in the string.
    # Send the command to the CPX in bytes format


    try:
        while True:

            cmd = input("Enter command (idle, alert, cool, quit): ")
            if cmd in ("idle", "alert", "cool"):
                # CPX expects a newline character at the end of the command, so we include '\n' in the string.
                # encode the command to bytes before sending
                message = (cmd + '\n').encode()  
                ser.write(message) 

                # Read and print the response from the CPX 
                read_response(ser)  
            else:
                if cmd == "quit":
                    break
                else:
                    print("Invalid command. Please enter 'idle', 'alert', or 'cool'.")
        # Close the serial connection when done
    except KeyboardInterrupt:
        print("\nExiting...")
    except serial.SerialException as e:
        print(f"Serial communication error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        ser.close()  
        print("Serial connection closed.")


if __name__ == "__main__":
    main()