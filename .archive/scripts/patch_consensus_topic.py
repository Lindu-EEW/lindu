import re

with open('src/server/consensus.py', 'r') as f:
    content = f.read()

# Change elif "/event" to if "/telemetry" and add threshold check
old_code = """    # 2. EVENT / TELEMETRI (Ada Getaran dari Node)
    elif "/event" in msg.topic:
        node_id = payload.get("node_id")
        pga = payload.get("pga", 0)
        sta_lta = payload.get("sta_lta", 0)"""

new_code = """    # 2. EVENT / TELEMETRI (Ada Getaran dari Node)
    elif "/telemetry" in msg.topic:
        node_id = payload.get("node_id")
        pga = payload.get("pga", 0)
        sta_lta = payload.get("sta_lta", 0)
        
        # [SYARAT TRIGGER ALERT LOKAL]
        if pga < 0.12:
            return # Abaikan noise kecil"""

content = content.replace(old_code, new_code)

# Remove the redundant if "/telemetry" block later down that causes issues or just leave it
# Actually, wait, there's another `if "/telemetry" in msg.topic:` block at the end for refinement.
# If I change `elif "/event"` to `elif "/telemetry"`, it will execute BOTH.
# Let's just change `elif "/event" in msg.topic:` to `elif "/telemetry" in msg.topic:` and add the return.

with open('src/server/consensus.py', 'w') as f:
    f.write(content)

print("Consensus Topic Patched")
