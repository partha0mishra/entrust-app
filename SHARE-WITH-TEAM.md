# 📤 Share This With Your Team

## One-Line Command (Copy & Paste)

### For Mac/Linux/Windows (Git Bash/WSL):

```bash
curl -L "https://drive.google.com/uc?export=download&id=1LDOOhQCsrP3zpdSujKWUVfndr4NFeAPD" -o docker-compose.standalone.yml && docker compose -f docker-compose.standalone.yml up
```

### For Windows PowerShell:

```powershell
Invoke-WebRequest -Uri "https://drive.google.com/uc?export=download&id=1LDOOhQCsrP3zpdSujKWUVfndr4NFeAPD" -OutFile "docker-compose.standalone.yml"; docker compose -f docker-compose.standalone.yml up
```

---

## What It Does

1. ✅ Downloads the docker-compose file from GitHub
2. ✅ Pulls images from Docker Hub (multi-platform: Windows, Mac Intel, Mac M1/M2/M3, Linux)
3. ✅ Starts PostgreSQL database
4. ✅ Starts Backend API (port 8000)
5. ✅ Starts Frontend (port 3000)
6. ✅ Auto-initializes database with admin user and 700 questions

## Access After Running

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

## Stop the Application

Press `Ctrl+C` or run:
```bash
docker compose -f docker-compose.standalone.yml down
```

---

**That's it! One command and you're running!** 🚀

