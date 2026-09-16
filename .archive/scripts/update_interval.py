with open('src/esp32_sensor_node/src/OtaUpdater.cpp', 'r') as f:
    content = f.read()

content = content.replace('millis() - _last_check > 300000', 'millis() - _last_check > 43200000 // 12 Jam')

with open('src/esp32_sensor_node/src/OtaUpdater.cpp', 'w') as f:
    f.write(content)
