with open('src/server/consensus.py', 'r') as f:
    content = f.read()

# Replace the tuple elements
content = content.replace(
    'payload.get("uptime", 0)\n            ))',
    'payload.get("uptime", 0),\n                payload.get("gas_raw", 0),\n                payload.get("gas_alert", False),\n                payload.get("door_status", "UNKNOWN"),\n                payload.get("valve_status", "UNKNOWN")\n            ))'
)

with open('src/server/consensus.py', 'w') as f:
    f.write(content)

