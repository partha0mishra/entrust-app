# 🚀 One-Line Command to Run Entrust

## For Your Teammates

### Option 1: Using curl (Mac, Linux, Windows with Git Bash/WSL) - Recommended

```bash
curl -L "https://drive.google.com/uc?export=download&id=1LDOOhQCsrP3zpdSujKWUVfndr4NFeAPD" -o docker-compose.standalone.yml && docker compose -f docker-compose.standalone.yml up
```

### Option 2: Using wget (Linux, Mac)

```bash
wget --no-check-certificate "https://drive.google.com/uc?export=download&id=1LDOOhQCsrP3zpdSujKWUVfndr4NFeAPD" -O docker-compose.standalone.yml && docker compose -f docker-compose.standalone.yml up
```

### Option 3: PowerShell (Windows)

```powershell
Invoke-WebRequest -Uri "https://drive.google.com/uc?export=download&id=1LDOOhQCsrP3zpdSujKWUVfndr4NFeAPD" -OutFile "docker-compose.standalone.yml"; docker compose -f docker-compose.standalone.yml up
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

