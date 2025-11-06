# PowerShell one-liner to run Entrust - Works on Windows

# Download docker-compose file from Google Drive and run
Invoke-WebRequest -Uri "https://drive.google.com/uc?export=download&id=1LDOOhQCsrP3zpdSujKWUVfndr4NFeAPD" -OutFile "docker-compose.standalone.yml"

docker compose -f docker-compose.standalone.yml up

