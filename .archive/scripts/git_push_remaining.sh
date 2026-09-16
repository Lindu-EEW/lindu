#!/bin/bash

# 1. lindu_actuator
cd "src/esp32_actuator_node"
git init
git add .
git commit -m "Production ready ESP32 Actuator Firmware"
git branch -M main
git remote add origin git@github.com:eatrisno/lindu_actuator.git
git push -u origin main -f
cd ../..

# 2. lindu_server
cd "src/server"
git init
git add .
git commit -m "Production ready Earthquake Consensus Engine"
git branch -M main
git remote add origin git@github.com:eatrisno/lindu_server.git
git push -u origin main -f
cd ../..

# 3. lindu (Master Repo)
git init
# Hanya tambahkan dokumen, docker-compose root, dan file penting (jangan masukkan repo anak)
git add docs/ README.md docker-compose.yml
git commit -m "Final Lindu Tesis Architecture and Documentation"
git branch -M main
git remote add origin git@github.com:eatrisno/lindu.git
git push -u origin main -f

