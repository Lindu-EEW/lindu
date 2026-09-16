import re

with open('.github/workflows/test.yml', 'r') as f:
    content = f.read()

target = 'pip install paho-mqtt psycopg2-binary'
replace = 'pip install -r src/server/requirements.txt'

content = content.replace(target, replace)

with open('.github/workflows/test.yml', 'w') as f:
    f.write(content)
