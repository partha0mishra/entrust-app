# Running Entrust from Docker Hub

## Quick Start (One Line)

```bash
docker compose -f docker-compose.hub.yml up
```

**Note:** Make sure to update `docker-compose.hub.yml` with your Docker Hub username first, or set it as an environment variable.

## Prerequisites

1. Docker and Docker Compose installed
2. Docker Hub account (for pulling images)
3. Update `docker-compose.hub.yml` with your Docker Hub username

## Setup Steps

1. **Update Docker Hub username in `docker-compose.hub.yml`:**
   - Replace `YOUR_DOCKERHUB_USERNAME` with your actual Docker Hub username

2. **Run the application:**
   ```bash
   docker compose -f docker-compose.hub.yml up
   ```

3. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Default Login Credentials

- **Admin:** `admin` / `Welcome123!`
- **CXO:** `emusk` / `Welcome123!`
- **Participants:** `Madhu` / `Welcome123!`, `Partha` / `Welcome123!`
- **Sales:** `Nagaraj` / `Welcome123!`

## What Gets Started

- **PostgreSQL Database** (port 5432)
- **Backend API** (port 8000)
- **Frontend** (port 3000)

The database will be automatically initialized with:
- Default admin user
- 700 survey questions
- Sample Tesla customer data (if using fill_tesla_data.py)

## Stopping the Application

```bash
docker compose -f docker-compose.hub.yml down
```

## Troubleshooting

- If images fail to pull, make sure you're logged into Docker Hub: `docker login`
- If ports are already in use, modify the port mappings in `docker-compose.hub.yml`
- Check logs: `docker compose -f docker-compose.hub.yml logs`

