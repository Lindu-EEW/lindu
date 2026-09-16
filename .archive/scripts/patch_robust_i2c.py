import re

with open('src/esp32_sensor_node/src/SensorManager.cpp', 'r') as f:
    content = f.read()

old_probe = """bool probeI2C(uint8_t address) {
  Wire1.beginTransmission(address);
  return (Wire1.endTransmission() == 0);
}"""

new_probe = """bool probeI2C(uint8_t address) {
  Wire1.setTimeOut(50); // Set timeout hanya untuk I2C Cuaca
  Wire1.beginTransmission(address);
  if (Wire1.endTransmission() == 0) {
    // Validasi ekstra: Coba baca 1 byte register ID (0xD0 untuk BMP/BME280)
    Wire1.beginTransmission(address);
    Wire1.write(0xD0);
    Wire1.endTransmission();
    if (Wire1.requestFrom(address, (uint8_t)1) == 1) {
      uint8_t id = Wire1.read();
      if (id == 0x58 || id == 0x60 || id == 0x56 || id == 0x57) { // ID valid BMP/BME
        return true;
      }
    }
  }
  return false;
}"""

content = content.replace(old_probe, new_probe)

with open('src/esp32_sensor_node/src/SensorManager.cpp', 'w') as f:
    f.write(content)

print("Robust I2C Probe Patched")
