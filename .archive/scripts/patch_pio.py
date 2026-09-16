with open('src/esp32_sensor_node/platformio.ini', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "-D PIN_I2C_SEIS_SCL=13" in line:
        lines.insert(i+1, "    -D PIN_GAS_MQ2=7\n")
        break

with open('src/esp32_sensor_node/platformio.ini', 'w') as f:
    f.writelines(lines)

