# EnTrust Application

## Quick Start (One Command)

```bash
docker-compose up
```

This will automatically:
- Start PostgreSQL database
- Deploy database (tables, admin user, questions)
- Start Backend API
- Start Frontend application

## Access URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Login Credentials

- **User ID**: `admin`
- **Password**: `admin123`

⚠️ **Change password in production!**

## Stopping the Application

Press `Ctrl+C` or run:
```bash
docker-compose down
```

## What's Included

- PostgreSQL 15 database
- FastAPI backend with automatic database deployment
- React frontend with Vite
- 700 survey questions pre-loaded
- All database migrations applied automatically

## Troubleshooting

**Check container status:**
```bash
docker-compose ps
```

**View logs:**
```bash
docker-compose logs backend
docker-compose logs frontend
```

**Rebuild containers:**
```bash
docker-compose up --build
```

**Fresh start (removes all data):**
```bash
docker-compose down -v
docker-compose up
```

## Database Deployment

The database is automatically deployed when the backend container starts. The deployment script (`backend/deploy_db.py`) handles:
- Creating all tables
- Creating admin user
- Loading questions from `questions.json`
- Running all migrations

No manual setup required!
