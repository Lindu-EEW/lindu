import re

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    content = f.read()

# Hapus blok #if !ARDUINO_USB_CDC_ON_BOOT di sekitar gas_alert dan door_status
# dan tambahkan gas_raw
content = re.sub(
    r'#if !ARDUINO_USB_CDC_ON_BOOT\s+// Field baru khusus unit ESP32 classic[^\n]*\n\s+// ditambahkan pada payload S3[^\n]*\n\s+doc\["door_status"\] = is_door_locked \? "LOCKED" : "UNLOCKED";\n\s+doc\["gas_alert"\] = sensorMgr\.gas_leak_detected;\n#endif',
    r'doc["door_status"] = is_door_locked ? "LOCKED" : "UNLOCKED";\n    doc["gas_alert"] = sensorMgr.gas_leak_detected;\n    doc["gas_raw"] = sensorMgr.gas_raw_value;',
    content
)

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
    f.write(content)

