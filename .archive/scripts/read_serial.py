import serial
import serial.tools.list_ports
import time

ports = list(serial.tools.list_ports.comports())
esp_port = None
for p in ports:
    if "usb" in p.device.lower() or "cu.usb" in p.device.lower() or "tty.usb" in p.device.lower() or "CH340" in p.description:
        esp_port = p.device
        break

if not esp_port:
    # default to the typical mac port
    esp_port = "/dev/cu.usbserial-0001"

print(f"Reading from {esp_port}...")
try:
    ser = serial.Serial(esp_port, 115200, timeout=1)
    # Restart the ESP32 to see boot logs!
    ser.setDTR(False)
    ser.setRTS(True)
    time.sleep(0.1)
    ser.setRTS(False)
    
    start_time = time.time()
    while time.time() - start_time < 15:
        line = ser.readline()
        if line:
            print(line.decode('utf-8', errors='ignore').strip())
except Exception as e:
    print(f"Error: {e}")
