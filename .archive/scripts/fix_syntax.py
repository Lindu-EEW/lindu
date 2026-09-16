import re

with open('src/server/consensus.py', 'r') as f:
    content = f.read()

content = content.replace('''    # Setup MQTT
    global mqtt_client
    mqtt_client = mqtt.Client("LinduServer_01")''', '''    # Setup MQTT
    mqtt_client = mqtt.Client("LinduServer_01")''')

with open('src/server/consensus.py', 'w') as f:
    f.write(content)
