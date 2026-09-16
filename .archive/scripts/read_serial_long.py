import serial
import serial.tools.list_ports
import time

esp_port = "/dev/cu.usbmodem101"
print(f"Reading from {esp_port} for 40 seconds...")
try:
    ser = serial.Serial(esp_port, 115200, timeout=1)
    ser.setDTR(False)
    ser.setRTS(True)
    time.sleep(0.1)
    ser.setRTS(False)
    
    start_time = time.time()
    while time.time() - start_time < 40:
        line = ser.readline()
        if line:
            print(line.decode('utf-8', errors='ignore').strip())
except Exception as e:
    print(f"Error: {e}")
