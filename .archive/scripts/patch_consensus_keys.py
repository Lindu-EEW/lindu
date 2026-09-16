import re

with open('src/server/consensus.py', 'r') as f:
    py = f.read()

py = py.replace('"epi_lat": float(t1["lat"]),', '"epicenter_lat": float(t1["lat"]),\n        "bypass": True,')
py = py.replace('"epi_lon": float(t1["lon"]),', '"epicenter_lon": float(t1["lon"]),')

with open('src/server/consensus.py', 'w') as f:
    f.write(py)

