import re

with open('src/esp32_sensor_node/src/OTAUpdater.h', 'r') as f:
    h = f.read()

# Hapus checkForUpdate() dari bagian private
h = h.replace('    void checkForUpdate();\n', '')

# Tambahkan checkForUpdate() ke bagian public (di bawah void loop();)
h = h.replace('    void loop();', '    void loop();\n    void checkForUpdate();')

# Update versi ke v1.1.35
h = h.replace('#define CURRENT_VERSION "v1.1.34"', '#define CURRENT_VERSION "v1.1.35"')

with open('src/esp32_sensor_node/src/OTAUpdater.h', 'w') as f:
    f.write(h)
