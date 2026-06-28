Have to set usb_cdc.enable(True) in boot.py so in data mode

Later add for others GitHub:
- function of finding the COM? of the data
This was when was tryign to use console + data

# import serial.tools.list_ports
# def find_cpx_port():
#     """Function to find the COM port of the CPX board. This is a placeholder and may need to be implemented based on your system."""
#     for port in serial.tools.list_ports.comports():
#         #VID:PID for CPX is 239A on my sytem, you may need to change it based on the COM port description of ypur CPX, can be found in Device Manager on Windows.
#         if "VID:PID=239A" in port.hwid:
#             return port.device
#         else:
#             print(port.description)
#     raise RuntimeError("CPX board not found. Please check the connection and try again.")
  

- try/exception

README.d with 
How to deal with boot.py