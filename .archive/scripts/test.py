import urllib.request
url = 'https://raw.githubusercontent.com/espressif/arduino-esp32/master/libraries/Update/src/Updater.cpp'
req = urllib.request.urlopen(url)
content = req.read().decode('utf-8')
if 'esp_ota_set_boot_partition' in content:
    print('FOUND esp_ota_set_boot_partition in Updater.cpp')
