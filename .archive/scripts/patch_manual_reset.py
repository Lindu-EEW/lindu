import re

# Update NetworkManager.h
with open('src/esp32_sensor_node/src/NetworkManager.h', 'r') as f:
    content = f.read()

if "extern bool is_valve_locked;" not in content:
    content = content.replace("extern unsigned long global_alarm_until;", "extern unsigned long global_alarm_until;\nextern bool is_valve_locked;")
    with open('src/esp32_sensor_node/src/NetworkManager.h', 'w') as f:
        f.write(content)

# Update NetworkManager.cpp
with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    content = f.read()

old_trigger = """            if (dist < 50.0 || is_bypass) {
                Serial.println("[!] SIRINE MENYALA! Epicenter berjarak < 50km (Atau Bypass Test).");
                global_alarm_until = millis() + 15000;
            } else {"""
            
new_trigger = """            if (dist < 50.0 || is_bypass) {
                Serial.println("[!] SIRINE MENYALA! Valve Dikunci Tutup!");
                global_alarm_until = millis() + 15000;
                is_valve_locked = true;
            } else {"""

content = content.replace(old_trigger, new_trigger)

old_reset = """            }
        }
    }
}

bool NetworkManager::isConnected() {"""

new_reset = """            }
        } else if (doc["cmd"] == "reset_valve") {
            Serial.println("[i] Sistem di-Reset Manual. Valve Dibuka.");
            is_valve_locked = false;
        }
    }
}

bool NetworkManager::isConnected() {"""

content = content.replace(old_reset, new_reset)

with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
    f.write(content)

# Update main.cpp
with open('src/esp32_sensor_node/src/main.cpp', 'r') as f:
    content = f.read()

# Add global var
if "bool is_valve_locked = false;" not in content:
    content = content.replace("unsigned long global_alarm_until = 0;", "unsigned long global_alarm_until = 0;\nbool is_valve_locked = false;")

# Fix servo logic in main loop
content = re.sub(r'// SIMULASI VALVE AIR/GAS.*?myServo\.write\(90\); // Putar 90 Derajat \(Tutup Katup!\)', '', content, flags=re.DOTALL)
content = re.sub(r'myServo\.write\(0\); // Valve Terbuka \(Standby\)', '', content, flags=re.DOTALL)

old_loop = "bool hw611_ok = sensorMgr.bme_ok || sensorMgr.bmp_ok;"
new_loop = """bool hw611_ok = sensorMgr.bme_ok || sensorMgr.bmp_ok;
            
            // LOGIKA VALVE MANUAL RESET
            if (is_valve_locked) {
                myServo.write(90); // Mengunci (Tutup) sampai direset
            } else {
                myServo.write(0);  // Normal (Buka)
            }"""

content = content.replace(old_loop, new_loop)

with open('src/esp32_sensor_node/src/main.cpp', 'w') as f:
    f.write(content)

print("Manual Reset Logic Patched")
