import re

with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    cpp = f.read()

# 1. Add Actuator Preferences logic
if "Preferences actPrefs;" not in cpp:
    cpp = cpp.replace('Preferences prefs;', 'Preferences prefs;\nPreferences actPrefs;')
    cpp = cpp.replace('bool is_valve_locked = false;', 'bool is_valve_locked = false;\nPreferences actPrefs;')
    
    setup_act = '''
    // Load state valve pasca-mati lampu
    actPrefs.begin("actuator", false);
    is_valve_locked = actPrefs.getBool("valve_locked", false);
    if (is_valve_locked) {
        Serial.println("[!] REBOOT PASCA GEMPA: Mengembalikan status Valve ke TERKUNCI demi keamanan!");
    }
'''
    cpp = cpp.replace('Serial.println("Memulai Node Sensor Lindu.id...");', 'Serial.println("Memulai Node Sensor Lindu.id...");\n' + setup_act)

# 2. Fix Epoch Precision
target_epoch = '''unsigned long getEpochTime() {
    time_t now;
    struct tm timeinfo;
    if (!getLocalTime(&timeinfo)) return 0;
    time(&now);
    return now;
}'''

replacement_epoch = '''double getEpochTime() {
    struct timeval tv;
    if (gettimeofday(&tv, NULL) != 0) return 0.0;
    return (double)tv.tv_sec + (double)tv.tv_usec / 1000000.0;
}'''

cpp = cpp.replace(target_epoch, replacement_epoch)

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(cpp)


# Fix NetworkManager.cpp headers
with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    nm = f.read()

# Fix precision signature
nm = nm.replace('unsigned long epoch', 'double epoch')

# Fix save valve to NVS
if "actPrefs.putBool" not in nm:
    nm = nm.replace('is_valve_locked = true;', 'is_valve_locked = true;\n                actPrefs.putBool("valve_locked", true);')
    nm = nm.replace('is_valve_locked = false;', 'is_valve_locked = false;\n                actPrefs.putBool("valve_locked", false);')
    nm = nm.replace('#include "NetworkManager.h"', '#include "NetworkManager.h"\n#include <Preferences.h>\nextern Preferences actPrefs;')

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
    f.write(nm)


with open('src/esp32_sensor_node/src/NetworkManager.h', 'r') as f:
    nmh = f.read()

nmh = nmh.replace('unsigned long epoch', 'double epoch')

with open('src/esp32_sensor_node/src/NetworkManager.h', 'w') as f:
    f.write(nmh)

with open('src/esp32_sensor_node/src/OTAUpdater.h', 'r') as f:
    oh = f.read()

oh = oh.replace('#define CURRENT_VERSION "v1.1.31"', '#define CURRENT_VERSION "v1.1.32"')

with open('src/esp32_sensor_node/src/OTAUpdater.h', 'w') as f:
    f.write(oh)

