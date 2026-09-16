import re

with open('src/server/consensus.py', 'r') as f:
    py = f.read()

py = py.replace('alarm_payload["epi_lat"]', 'alarm_payload["epicenter_lat"]')
py = py.replace('alarm_payload["epi_lon"]', 'alarm_payload["epicenter_lon"]')

# And in ALARM_UPDATE
py = py.replace('"epi_lat": refined_lat,', '"epicenter_lat": refined_lat,')
py = py.replace('"epi_lon": refined_lon,', '"epicenter_lon": refined_lon,')

with open('src/server/consensus.py', 'w') as f:
    f.write(py)

