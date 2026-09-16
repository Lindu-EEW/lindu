import re

# 1. Update requirements.txt
with open('prototype/grafana-stack/ingester/requirements.txt', 'a') as f:
    f.write('\nflask\nflask-cors\n')

# 2. Update docker-compose.yml
with open('prototype/grafana-stack/docker-compose.yml', 'r') as f:
    compose = f.read()

compose = compose.replace('''    environment:
      MQTT_HOST: mosquitto
      DB_HOST: postgres''', '''    environment:
      MQTT_HOST: mosquitto
      DB_HOST: postgres
    ports:
      - "5000:5000"''')

compose = compose.replace('''      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_AUTH_ANONYMOUS_ENABLED=true''', '''      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_AUTH_ANONYMOUS_ENABLED=true
      - GF_PANELS_DISABLE_SANITIZE_HTML=true''')

with open('prototype/grafana-stack/docker-compose.yml', 'w') as f:
    f.write(compose)

# 3. Update ingester.py
with open('prototype/grafana-stack/ingester/ingester.py', 'r') as f:
    ing = f.read()

# Add Flask imports
ing = ing.replace('import os', 'import os\nfrom flask import Flask, request, jsonify\nfrom flask_cors import CORS')

# Change mqtt loop from loop_forever to loop_start, and start Flask
ing = ing.replace('client.loop_forever()', '''
# Jalankan MQTT di background
client.loop_start()

# Setup Flask API
app = Flask(__name__)
CORS(app)

@app.route('/api/cmd', methods=['POST'])
def send_cmd():
    try:
        data = request.json
        cmd = data.get('cmd')
        target = data.get('target_node', 'all')
        if not cmd:
            return jsonify({"error": "Missing cmd"}), 400
            
        payload = {"cmd": cmd, "target_node": target}
        client.publish("lindu/actuator/cmd/all", json.dumps(payload))
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
''')

with open('prototype/grafana-stack/ingester/ingester.py', 'w') as f:
    f.write(ing)

