import re

with open('src/esp32_sensor_node/src/SensorManager.cpp', 'r') as f:
    content = f.read()

target = """  static unsigned long last_cuaca_check = 0;
  if (!bme_ok && !bmp_ok && millis() - last_cuaca_check > 5000) {
    bme_ok = _bme.begin(0x76, &Wire1) || _bme.begin(0x77, &Wire1);
    if (!bme_ok)
      bmp_ok = _bmp->begin(0x76) || _bmp->begin(0x77);
    last_cuaca_check = millis();
  }"""

new_code = """  static unsigned long last_cuaca_check = 0;
  static int cuaca_retry_count = 0;
  
  if (!bme_ok && !bmp_ok && cuaca_retry_count < 3 && millis() - last_cuaca_check > 5000) {
    cuaca_retry_count++;
    bme_ok = _bme.begin(0x76, &Wire1) || _bme.begin(0x77, &Wire1);
    if (!bme_ok)
      bmp_ok = _bmp->begin(0x76) || _bmp->begin(0x77);
    last_cuaca_check = millis();
  }"""

content = content.replace(target, new_code)

with open('src/esp32_sensor_node/src/SensorManager.cpp', 'w') as f:
    f.write(content)

print("Retry Limit Patched")
