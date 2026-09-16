#!/bin/bash

# 1. lindu_grafana
cd "prototype/grafana-stack"
git init
git add .
git commit -m "Production ready Grafana Stack"
git branch -M main
git remote add origin git@github.com:eatrisno/lindu_grafana.git
git push -u origin main -f
cd ../..

# 2. lindu_node
cd "src/esp32_sensor_node"
git init
git add .
git commit -m "Production ready ESP32 firmware with OTA"
git branch -M main
git remote add origin git@github.com:eatrisno/lindu_node.git
git push -u origin main -f
cd ../..

# 3. lindu_frontend
cd "src/dashboard"
git init
git add .
git commit -m "Production ready Frontend Dashboard"
git branch -M main
git remote add origin git@github.com:eatrisno/lindu_frontend.git
git push -u origin main -f
cd ../..

