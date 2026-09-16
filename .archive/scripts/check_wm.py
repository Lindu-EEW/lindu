import urllib.request
url = 'https://raw.githubusercontent.com/tzapu/WiFiManager/master/WiFiManager.h'
try:
    req = urllib.request.urlopen(url)
    content = req.read().decode('utf-8')
    for line in content.split('\n'):
        if 'WiFiManagerParameter(' in line:
            print(line.strip())
except:
    pass
