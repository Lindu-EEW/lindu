import re

with open('prototype/grafana-stack/ingester/ingester.py', 'r') as f:
    content = f.read()

target = '''        if cmd == "set_location":
            payload["lat"] = float(data.get("lat", 0.0))
            payload["lon"] = float(data.get("lon", 0.0))'''

replace = '''        if cmd == "set_location":
            payload["lat"] = float(data.get("lat", 0.0))
            payload["lon"] = float(data.get("lon", 0.0))
        elif cmd == "set_broker":
            payload["server"] = data.get("server", "192.168.68.105")'''

content = content.replace(target, replace)

with open('prototype/grafana-stack/ingester/ingester.py', 'w') as f:
    f.write(content)
