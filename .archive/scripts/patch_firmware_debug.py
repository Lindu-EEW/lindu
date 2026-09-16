import re

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    nmc = f.read()

# 1. Add global variable
nmc = nmc.replace('#include "NetworkManager.h"', '#include "NetworkManager.h"\n\nbool remote_debug_enabled = false;\n')

# 2. Modify publishLog to check the flag
target_pub = '''void NetworkManager::publishLog(const char* message) {
    if (!mqtt.connected()) return;'''

replacement_pub = '''void NetworkManager::publishLog(const char* message) {
    if (!mqtt.connected()) return;
    if (!remote_debug_enabled) return; // Hanya kirim log jika user menekan ENABLE DEBUG di Grafana
'''
nmc = nmc.replace(target_pub, replacement_pub)

# 3. Add MQTT command listener
target_cmd = '''            } else if (cmd == "enable_valve") {
                is_valve_locked = false;
                actPrefs.putBool("valve_locked", false);
                Serial.println("[!] PERINTAH REMOTE: Membuka Valve/Pintu!");
            }'''

replacement_cmd = '''            } else if (cmd == "enable_valve") {
                is_valve_locked = false;
                actPrefs.putBool("valve_locked", false);
                Serial.println("[!] PERINTAH REMOTE: Membuka Valve/Pintu!");
            } else if (cmd == "enable_debug") {
                remote_debug_enabled = true;
                Serial.println("[!] PERINTAH REMOTE: Mode Debug Diaktifkan.");
                instance->publishLog("Mode Stream Log Berhasil Diaktifkan! Alat siap dimonitor.");
            } else if (cmd == "disable_debug") {
                instance->publishLog("Mode Stream Log Dinonaktifkan.");
                remote_debug_enabled = false;
                Serial.println("[!] PERINTAH REMOTE: Mode Debug Dimatikan.");
            }'''
nmc = nmc.replace(target_cmd, replacement_cmd)

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
    f.write(nmc)

# Bump version to v1.3.2
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'r') as f:
    oh = f.read()
oh = oh.replace('#define CURRENT_VERSION "v1.3.1"', '#define CURRENT_VERSION "v1.3.2"')
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'w') as f:
    f.write(oh)

