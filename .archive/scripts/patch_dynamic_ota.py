import re

# 1. Update ConfigManager.h
with open('src/esp32_sensor_node/src/ConfigManager.h', 'r') as f:
    cmh = f.read()
cmh = cmh.replace('char mqtt_server[64];', 'char mqtt_server[64];\n    char ota_repo[64];')
with open('src/esp32_sensor_node/src/ConfigManager.h', 'w') as f:
    f.write(cmh)

# 2. Update ConfigManager.cpp
with open('src/esp32_sensor_node/src/ConfigManager.cpp', 'r') as f:
    cmc = f.read()

load_cfg_target = 'config.is_provisioned = (config.lat != 0.0);'
load_cfg_replace = '''config.is_provisioned = (config.lat != 0.0);
    String repo = prefs.getString("ota_repo", "Lindu-EEW/lindu_node");
    strlcpy(config.ota_repo, repo.c_str(), sizeof(config.ota_repo));'''
cmc = cmc.replace(load_cfg_target, load_cfg_replace)

save_cfg_target = 'prefs.putString("mqtt_srv", config.mqtt_server);'
save_cfg_replace = '''prefs.putString("mqtt_srv", config.mqtt_server);
    prefs.putString("ota_repo", config.ota_repo);'''
cmc = cmc.replace(save_cfg_target, save_cfg_replace)

portal_target1 = 'WiFiManagerParameter custom_mqtt("mqtt", "MQTT Broker IP/Domain", config.mqtt_server, 64);'
portal_replace1 = '''WiFiManagerParameter custom_repo("repo", "GitHub OTA Repo", config.ota_repo, 64);
    wm.addParameter(&custom_repo);
    WiFiManagerParameter custom_mqtt("mqtt", "MQTT Broker IP/Domain", config.mqtt_server, 64);'''
cmc = cmc.replace(portal_target1, portal_replace1)

portal_target2 = 'strlcpy(config.mqtt_server, custom_mqtt.getValue(), sizeof(config.mqtt_server));'
portal_replace2 = '''strlcpy(config.mqtt_server, custom_mqtt.getValue(), sizeof(config.mqtt_server));
    strlcpy(config.ota_repo, custom_repo.getValue(), sizeof(config.ota_repo));'''
cmc = cmc.replace(portal_target2, portal_replace2)

with open('src/esp32_sensor_node/src/ConfigManager.cpp', 'w') as f:
    f.write(cmc)


# 3. Update OTAUpdater.h
with open('src/esp32_sensor_node/src/OTAUpdater.h', 'r') as f:
    oh = f.read()

oh = oh.replace('#define REPO_OWNER "Lindu-EEW"\n#define REPO_NAME "lindu_node"\n', '')
oh = oh.replace('#define CURRENT_VERSION "v1.1.27"', '#define CURRENT_VERSION "v1.1.28"')

with open('src/esp32_sensor_node/src/OTAUpdater.h', 'w') as f:
    f.write(oh)

# 4. Update OTAUpdater.cpp
with open('src/esp32_sensor_node/src/OTAUpdater.cpp', 'r') as f:
    oc = f.read()

oc_inc = '#include "OTAUpdater.h"\n#include "ConfigManager.h"\nextern ConfigManager configMgr;\n'
oc = oc.replace('#include "OTAUpdater.h"\n', oc_inc)

url_target = 'String url = String("https://api.github.com/repos/") + REPO_OWNER + "/" + REPO_NAME + "/releases/latest";'
url_replace = 'String url = String("https://api.github.com/repos/") + configMgr.config.ota_repo + "/releases/latest";'
oc = oc.replace(url_target, url_replace)

with open('src/esp32_sensor_node/src/OTAUpdater.cpp', 'w') as f:
    f.write(oc)

