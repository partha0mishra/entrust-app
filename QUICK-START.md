# 🚀 Quick Start - Run Entrust in One Command

## For Your Teammates (Windows, Mac, Linux)

**Simply run this command:**

```bash
docker compose -f docker-compose.standalone.yml up
```

**Works on:** ✅ Windows, ✅ macOS, ✅ Linux (with Docker Desktop or Docker Engine)

**That's it!** No local files needed - everything runs from Docker Hub images.

---

### Alternative: With Local Development Files

If you have the repository cloned and want hot-reloading:

```bash
docker compose -f docker-compose.hub.yml up
```

That's it! The application will start with:
- ✅ PostgreSQL database (auto-initialized)
- ✅ Backend API on http://localhost:8000
- ✅ Frontend on http://localhost:3000

## Default Login Credentials

- **Admin:** `admin` / `Welcome123!`
- **CXO:** `emusk` / `Welcome123!`
- **Participants:** `Madhu` / `Welcome123!`, `Partha` / `Welcome123!`
- **Sales:** `Nagaraj` / `Welcome123!`

## Prerequisites

- **Docker Desktop** (Windows/Mac) or **Docker Engine + Docker Compose** (Linux)
- Ports 3000, 8000, and 5432 available
- **No local files required** - everything runs from Docker Hub images!
- Works on **Windows, macOS, and Linux** - fully platform-independent

## Access Points

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs

## Stop the Application

```bash
# For standalone version
docker compose -f docker-compose.standalone.yml down

# For development version
docker compose -f docker-compose.hub.yml down
```

## Platform Support

✅ **Windows** - Works with Docker Desktop  
✅ **macOS** - Works with Docker Desktop  
✅ **Linux** - Works with Docker Engine + Docker Compose  

All paths, commands, and configurations are platform-independent!

---

**Note:** The first time you run this, Docker will pull the images from Docker Hub (kshitij001/entrust-backend and kshitij001/entrust-frontend), which may take a few minutes.

