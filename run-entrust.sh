#!/bin/bash
# One-line command to run Entrust - Works on Windows (Git Bash/WSL), Mac, Linux

# Download docker-compose file from Google Drive and run
curl -L "https://drive.google.com/uc?export=download&id=1LDOOhQCsrP3zpdSujKWUVfndr4NFeAPD" -o docker-compose.standalone.yml 2>/dev/null || \
wget --no-check-certificate "https://drive.google.com/uc?export=download&id=1LDOOhQCsrP3zpdSujKWUVfndr4NFeAPD" -O docker-compose.standalone.yml 2>/dev/null || \
echo "Error: Could not download docker-compose file. Please ensure curl or wget is installed."

docker compose -f docker-compose.standalone.yml up

