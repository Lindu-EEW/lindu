with open('src/esp32_sensor_node/src/NetworkManager.h', 'r') as f:
    h = f.read()

target = 'void publishEvent(float pga, float sta_lta, int freq_hz, float ax, float ay, float az, unsigned long uptime_ms, double epoch, float lat, float lon, float temp, float pres);'
replacement = target + '\\n    void publishLog(const char* message);'

h = h.replace(target, replacement)

with open('src/esp32_sensor_node/src/NetworkManager.h', 'w') as f:
    f.write(h)

# Bump version to v1.3.1
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'r') as f:
    oh = f.read()
oh = oh.replace('#define CURRENT_VERSION "v1.3.0"', '#define CURRENT_VERSION "v1.3.1"')
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'w') as f:
    f.write(oh)
