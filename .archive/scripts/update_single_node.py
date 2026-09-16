import paho.mqtt.client as mqtt
import json
import time

payload = {
    "cmd": "set_location",
    "target_node": "node_3c096f0c",
    "lat": 35.5602687,
    "lon": 139.4767411
}

client = mqtt.Client()
client.connect("localhost", 1883, 60)
client.loop_start()

client.publish("lindu/actuator/cmd/all", json.dumps(payload))
print(f"Sent location update to {payload['target_node']}")
time.sleep(1)

client.loop_stop()
client.disconnect()
