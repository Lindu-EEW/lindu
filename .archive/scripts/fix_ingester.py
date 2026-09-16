with open('prototype/grafana-stack/ingester/ingester.py', 'r') as f:
    content = f.read()

if "import threading" not in content:
    content = "import threading\n" + content

with open('prototype/grafana-stack/ingester/ingester.py', 'w') as f:
    f.write(content)
