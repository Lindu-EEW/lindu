import re

with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    cpp = f.read()

target = '''            breathAngle += 0.05;
            if (breathAngle > 2 * PI) breathAngle -= 2 * PI;
            int brightness = (sin(breathAngle) + 1.0) * 20.0;'''

replacement = '''            breathAngle += 0.05;
            if (breathAngle > 2 * PI) breathAngle -= 2 * PI;
            // Mode "Kamar Tidur": Diturunkan dari pengali 20.0 menjadi 3.0 (Kecerahan max hanya 6/255)
            // LED akan bernafas dengan sangat, sangat redup dan tidak menyilaukan saat lampu kamar dimatikan.
            int brightness = (sin(breathAngle) + 1.0) * 3.0;'''

cpp = cpp.replace(target, replacement)

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(cpp)

# Bump version to v1.3.0 (Major Polish)
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'r') as f:
    oh = f.read()
oh = oh.replace('#define CURRENT_VERSION "v1.2.9"', '#define CURRENT_VERSION "v1.3.0"')
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'w') as f:
    f.write(oh)

