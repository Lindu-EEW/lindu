with open('src/server/consensus.py', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "def fire_alarm(" in line:
        for j in range(i, i+60):
            if "client.publish(TOPIC_ALARM, json.dumps(payload))" in lines[j]:
                lines[j] = """    # Broadcast alarm ke semua kemungkinan topik sensor dan aktuator
    client.publish(TOPIC_ALARM, json.dumps(payload))
    client.publish("lindu/actuator/cmd/all", json.dumps(payload))
    client.publish("lindu/sensor/cmd/all", json.dumps(payload))
"""
                break
        break

with open('src/server/consensus.py', 'w') as f:
    f.writelines(lines)

