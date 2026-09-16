with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    content = f.read()

content = content.replace("sendCmd('valve_lock')", "sendCmd('disable_valve')")
content = content.replace("sendCmd('valve_unlock')", "sendCmd('enable_valve')")

with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    f.write(content)
