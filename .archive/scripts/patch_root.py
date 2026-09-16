import re

with open('src/server/consensus.py', 'r') as f:
    content = f.read()

root_route = '''@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "status": "online",
        "service": "Lindu.id Consensus & API Engine",
        "endpoints": [
            "/api/history",
            "/api/nodes",
            "/api/metrics",
            "/api/cmd"
        ]
    })

@app.route('/api/history', methods=['GET'])'''

if "@app.route('/', methods=['GET'])" not in content:
    content = content.replace("@app.route('/api/history', methods=['GET'])", root_route)
    with open('src/server/consensus.py', 'w') as f:
        f.write(content)
