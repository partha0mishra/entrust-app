# 🚀 One-Line Command to Run Entrust

## For Your Teammates

### Option 1: Using curl (Mac, Linux, Windows with Git Bash/WSL)

```bash
curl -o docker-compose.standalone.yml https://raw.githubusercontent.com/partha0mishra/entrust-app/docker_deploy/docker-compose.standalone.yml && docker compose -f docker-compose.standalone.yml up
```

### Option 2: Using wget (Linux, Mac)

```bash
wget -O docker-compose.standalone.yml https://raw.githubusercontent.com/partha0mishra/entrust-app/docker_deploy/docker-compose.standalone.yml && docker compose -f docker-compose.standalone.yml up
```

### Option 3: PowerShell (Windows)

```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/partha0mishra/entrust-app/docker_deploy/docker-compose.standalone.yml" -OutFile "docker-compose.standalone.yml"; docker compose -f docker-compose.standalone.yml up
```

### Option 4: Direct from URL (Docker Compose 2.20+)

```bash
docker compose -f https://raw.githubusercontent.com/partha0mishra/entrust-app/docker_deploy/docker-compose.standalone.yml up
```

---

## What Happens

1. Downloads the `docker-compose.standalone.yml` file from GitHub
2. Pulls images from Docker Hub (kshitij001/entrust-backend, kshitij001/entrust-frontend)
3. Starts PostgreSQL, Backend, and Frontend
4. Auto-initializes database with admin user and questions

## Access

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## Login Credentials

- **Admin:** `admin` / `Welcome123!`
- **CXO:** `emusk` / `Welcome123!`
- **Participants:** `Madhu` / `Welcome123!`, `Partha` / `Welcome123!`
- **Sales:** `Nagaraj` / `Welcome123!`

## Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine + Compose (Linux)
- Ports 3000, 8000, 5432 available

---

**That's it! One command and you're running!** 🎉

