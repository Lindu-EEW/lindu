import re

# 1. Update NetworkManager.cpp
with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'r') as f:
    nm = f.read()

target = '''        } else if (doc["cmd"] == "force_update" || doc["cmd"] == "reboot") {'''
replacement = '''        } else if (doc["cmd"] == "factory_reset") {
            String target = doc["target_node"] | "all";
            String my_id = String(instance->_configMgr->config.node_id);
            if (target == "all" || target == my_id) {
                Serial.println("[!] Perintah Sistem: FACTORY RESET. Menghapus semua memori dan Restart...");
                instance->_configMgr->resetConfig(); // Hapus WiFi & Koordinat
                Preferences prefs;
                prefs.begin("ota", false);
                prefs.clear(); // Hapus blacklist OTA
                prefs.end();
                delay(1000);
                ESP.restart();
            }
        } else if (doc["cmd"] == "force_update" || doc["cmd"] == "reboot") {'''

if "factory_reset" not in nm:
    nm = nm.replace(target, replacement)
    with open('src/esp32_sensor_node/src/NetworkManager.cpp', 'w') as f:
        f.write(nm)

# 2. Update React CommandCenterPanel.jsx
with open('src/dashboard-react/src/components/CommandCenterPanel.jsx', 'r') as f:
    cc = f.read()

target_ui = '''<div className="flex gap-2">
                                <button onClick={() => sendCommand('identify', n.id)} className="flex-1 flex justify-center items-center gap-1 bg-gray-800 hover:bg-gray-600 text-white text-[10px] py-1.5 rounded border border-gray-600 transition">
                                    <Lightbulb size={12} /> Identify
                                </button>
                                <button onClick={() => sendCommand('force_update', n.id)} className="flex-1 flex justify-center items-center gap-1 bg-blue-900/50 hover:bg-blue-700 text-blue-200 text-[10px] py-1.5 rounded border border-blue-700 transition">
                                    <DownloadCloud size={12} /> OTA
                                </button>
                            </div>'''

replace_ui = '''<div className="flex gap-2">
                                <button onClick={() => sendCommand('identify', n.id)} className="flex-1 flex justify-center items-center gap-1 bg-gray-800 hover:bg-gray-600 text-white text-[10px] py-1.5 rounded border border-gray-600 transition">
                                    <Lightbulb size={12} /> Identify
                                </button>
                                <button onClick={() => sendCommand('force_update', n.id)} className="flex-1 flex justify-center items-center gap-1 bg-blue-900/50 hover:bg-blue-700 text-blue-200 text-[10px] py-1.5 rounded border border-blue-700 transition">
                                    <DownloadCloud size={12} /> OTA
                                </button>
                                <button onClick={() => { if(window.confirm('Yakin ingin mereset WiFi & Koordinat node ini? Node akan terputus.')) sendCommand('factory_reset', n.id) }} className="flex-1 flex justify-center items-center gap-1 bg-red-900/80 hover:bg-red-600 text-white text-[10px] py-1.5 rounded border border-red-500 transition font-bold">
                                    Reset
                                </button>
                            </div>'''

if "factory_reset" not in cc:
    cc = cc.replace(target_ui, replace_ui)
    with open('src/dashboard-react/src/components/CommandCenterPanel.jsx', 'w') as f:
        f.write(cc)

# Bump version to 1.1.13
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'r') as f:
    oh = f.read()
oh = oh.replace('#define CURRENT_VERSION "v1.1.12"', '#define CURRENT_VERSION "v1.1.13"')
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'w') as f:
    f.write(oh)

