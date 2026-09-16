# Fix docker-compose.yml
with open('prototype/grafana-stack/docker-compose.yml', 'r') as f:
    c = f.read()
c = c.replace('- "5000:5000"', '- "5001:5000"')
with open('prototype/grafana-stack/docker-compose.yml', 'w') as f:
    f.write(c)

# Fix seismic.json
with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'r') as f:
    s = f.read()
s = s.replace('http://localhost:5000/api/cmd', 'http://localhost:5001/api/cmd')
with open('prototype/grafana-stack/grafana/dashboards/seismic.json', 'w') as f:
    f.write(s)
