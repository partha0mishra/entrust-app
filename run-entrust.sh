#!/bin/bash
# One-line command to run Entrust - Works on Windows (Git Bash/WSL), Mac, Linux

# Download docker-compose file and run
curl -o docker-compose.standalone.yml https://raw.githubusercontent.com/partha0mishra/entrust-app/docker_deploy/docker-compose.standalone.yml 2>/dev/null || \
wget -O docker-compose.standalone.yml https://raw.githubusercontent.com/partha0mishra/entrust-app/docker_deploy/docker-compose.standalone.yml 2>/dev/null || \
echo "Error: Could not download docker-compose file. Please ensure curl or wget is installed."

docker compose -f docker-compose.standalone.yml up

