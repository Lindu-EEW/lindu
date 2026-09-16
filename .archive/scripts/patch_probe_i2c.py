import re

with open('src/esp32_sensor_node/src/SensorManager.cpp', 'r') as f:
    content = f.read()

probe_func = """bool probeI2C(uint8_t address) {
  Wire1.beginTransmission(address);
  return (Wire1.endTransmission() == 0);
}
"""

if "probeI2C" not in content:
    content = content.replace("void SensorManager::begin(QueueHandle_t queue) {", probe_func + "\nvoid SensorManager::begin(QueueHandle_t queue) {")

old_begin = """  bme_ok = _bme.begin(0x76, &Wire1) || _bme.begin(0x77, &Wire1);
  if (!bme_ok)
    bmp_ok = _bmp->begin(0x76) || _bmp->begin(0x77);"""

new_begin = """  // PROBE I2C DULU UNTUK MENCEGAH HANG
  if (probeI2C(0x76) || probeI2C(0x77)) {
    bme_ok = _bme.begin(0x76, &Wire1) || _bme.begin(0x77, &Wire1);
    if (!bme_ok) {
      bmp_ok = _bmp->begin(0x76) || _bmp->begin(0x77);
    }
  } else {
    bme_ok = false;
    bmp_ok = false;
  }"""
content = content.replace(old_begin, new_begin)


old_loop = """  if (!bme_ok && !bmp_ok && cuaca_retry_count < 3 && millis() - last_cuaca_check > 5000) {
    cuaca_retry_count++;
    bme_ok = _bme.begin(0x76, &Wire1) || _bme.begin(0x77, &Wire1);
    if (!bme_ok)
      bmp_ok = _bmp->begin(0x76) || _bmp->begin(0x77);
    last_cuaca_check = millis();
  }"""

new_loop = """  if (!bme_ok && !bmp_ok && cuaca_retry_count < 3 && millis() - last_cuaca_check > 5000) {
    cuaca_retry_count++;
    if (probeI2C(0x76) || probeI2C(0x77)) {
      bme_ok = _bme.begin(0x76, &Wire1) || _bme.begin(0x77, &Wire1);
      if (!bme_ok) {
        bmp_ok = _bmp->begin(0x76) || _bmp->begin(0x77);
      }
    }
    last_cuaca_check = millis();
  }"""
content = content.replace(old_loop, new_loop)

with open('src/esp32_sensor_node/src/SensorManager.cpp', 'w') as f:
    f.write(content)

print("I2C Probe Patched")
