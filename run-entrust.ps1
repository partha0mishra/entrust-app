# PowerShell one-liner to run Entrust - Works on Windows

# Download docker-compose file and run
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/partha0mishra/entrust-app/docker_deploy/docker-compose.standalone.yml" -OutFile "docker-compose.standalone.yml"

docker compose -f docker-compose.standalone.yml up

