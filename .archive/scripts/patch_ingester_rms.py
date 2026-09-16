import re

with open('prototype/grafana-stack/ingester/ingester.py', 'r') as f:
    content = f.read()

content = content.replace('rms = payload.get("rms", 0.0)', 'rms = payload.get("sta_lta", payload.get("rms", 0.0))')

with open('prototype/grafana-stack/ingester/ingester.py', 'w') as f:
    f.write(content)

print("Ingester Patched")
