import re

with open('src/server/consensus.py', 'r') as f:
    py = f.read()

py = py.replace('"epi_lat": epi_lat,', '"epicenter_lat": epi_lat,')
py = py.replace('"epi_lon": epi_lon,', '"epicenter_lon": epi_lon,')

with open('src/server/consensus.py', 'w') as f:
    f.write(py)

