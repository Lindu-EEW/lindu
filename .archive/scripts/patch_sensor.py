import re

with open('src/esp32_sensor_node/src/SensorManager.cpp', 'r') as f:
    content = f.read()

# Hapus blok #if !ARDUINO_USB_CDC_ON_BOOT di dalam begin()
content = re.sub(r'#if !ARDUINO_USB_CDC_ON_BOOT\s+// Sensor gas MQ-2 hanya ada di unit ESP32 classic \(esp32_wroom\)\s+pinMode\(PIN_GAS_MQ2, INPUT\);\s+_gas_boot_time = millis\(\);\s+#endif', 
                 r'// Sensor gas MQ-2 sekarang diaktifkan untuk semua unit\n  pinMode(PIN_GAS_MQ2, INPUT);\n  _gas_boot_time = millis();', 
                 content)

# Hapus blok #if !ARDUINO_USB_CDC_ON_BOOT di definisi readGasSensor()
content = re.sub(r'#if !ARDUINO_USB_CDC_ON_BOOT\s+// Sensor gas MQ-2: fitur ini HANYA untuk unit ESP32 classic \(esp32_wroom\)\.\s+// Dibungkus preprocessor supaya sama sekali tidak ter-compile/tereksekusi\s+// pada build ESP32-S3 \(mencegah GPIO S3 yang belum terpakai membaca noise\s+// dan secara tidak sengaja memicu is_valve_locked=true\)\.\s+(void SensorManager::readGasSensor\(\) \{[\s\S]*?\n\})\s+#endif', 
                 r'// Sensor gas MQ-2 diaktifkan lintas platform.\n\1', 
                 content)

# Hapus blok #if !ARDUINO_USB_CDC_ON_BOOT di loop()
content = re.sub(r'#if !ARDUINO_USB_CDC_ON_BOOT\s+readGasSensor\(\);\s+#endif', 
                 r'readGasSensor();', 
                 content)

with open('src/esp32_sensor_node/src/SensorManager.cpp', 'w') as f:
    f.write(content)

