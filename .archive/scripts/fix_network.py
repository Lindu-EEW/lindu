with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    content = f.read()

# Replace the door_status and gas_alert lines with proper ifdef for door
old_lines = """    doc["valve_status"] = is_valve_locked ? "DISABLED" : "ENABLED";
doc["door_status"] = is_door_locked ? "LOCKED" : "UNLOCKED";
    doc["gas_alert"] = sensorMgr.gas_leak_detected;
    doc["gas_raw"] = sensorMgr.gas_raw_value;"""

new_lines = """    doc["valve_status"] = is_valve_locked ? "DISABLED" : "ENABLED";
#if !ARDUINO_USB_CDC_ON_BOOT
    doc["door_status"] = is_door_locked ? "LOCKED" : "UNLOCKED";
#else
    doc["door_status"] = "UNAVAILABLE";
#endif
    doc["gas_alert"] = sensorMgr.gas_leak_detected;
    doc["gas_raw"] = sensorMgr.gas_raw_value;"""

content = content.replace(old_lines, new_lines)

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
    f.write(content)

