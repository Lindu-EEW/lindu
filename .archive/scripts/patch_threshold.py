with open('src/esp32_sensor_node/src/SensorManager.h', 'r') as f:
    content = f.read()

content = content.replace('#define GAS_LEAK_THRESHOLD 1800', '#define GAS_LEAK_THRESHOLD 3700')

with open('src/esp32_sensor_node/src/SensorManager.h', 'w') as f:
    f.write(content)

