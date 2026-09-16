import re
with open('src/server/consensus.py', 'r') as f:
    content = f.read()
content = content.replace("if pga >= 0.05:", "if pga >= 0.12:")
content = content.replace("PGA 0.05G", "PGA 0.12G")
with open('src/server/consensus.py', 'w') as f:
    f.write(content)
print("Consensus Threshold Patched")
