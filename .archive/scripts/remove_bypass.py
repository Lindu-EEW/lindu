import re

with open('src/server/consensus.py', 'r') as f:
    py = f.read()

# Hapus baris bypass
py = py.replace('        "bypass": True,\n', '')

with open('src/server/consensus.py', 'w') as f:
    f.write(py)

