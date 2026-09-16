import re

with open('src/esp32_sensor_node/src/SensorManager.cpp', 'r') as f:
    content = f.read()

old_wire = """  Wire.begin(12, 13);  // Akselerometer
  Wire1.begin(10, 11); // Cuaca"""
new_wire = """  Wire.begin(12, 13);  // Akselerometer
  Wire1.begin(10, 11); // Cuaca
  Wire.setTimeOut(20); // 20ms timeout untuk mencegah Hang di Core 1
  Wire1.setTimeOut(20);"""

content = content.replace(old_wire, new_wire)

with open('src/esp32_sensor_node/src/SensorManager.cpp', 'w') as f:
    f.write(content)

print("I2C Timeout Patched")
