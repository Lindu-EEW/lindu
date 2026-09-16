import re

with open('prototype/grafana-stack/ingester/ingester.py', 'r') as f:
    content = f.read()

content = content.replace("topic = msg.topic", "topic = msg.topic\n        print(f'Received: {topic}')")

with open('prototype/grafana-stack/ingester/ingester.py', 'w') as f:
    f.write(content)
