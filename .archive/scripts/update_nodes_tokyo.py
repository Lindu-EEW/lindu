import paho.mqtt.client as mqtt
import json
import time

nodes = [
    {
        "cmd": "set_location",
        "target_node": "node_2418399e",
        "lat": 35.5325783,
        "lon": 139.4462449
    },
    {
        "cmd": "set_location",
        "target_node": "node_acbd13f9",
        "lat": 35.6684103,
        "lon": 139.5760603
    }
]

client = mqtt.Client()
client.connect("localhost", 1883, 60)
client.loop_start()

for payload in nodes:
    client.publish("lindu/actuator/cmd/all", json.dumps(payload))
    print(f"Sent location update to {payload['target_node']}: {payload['lat']}, {payload['lon']}")
    time.sleep(1)

client.loop_stop()
client.disconnect()
