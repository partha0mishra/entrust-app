# EnTrust Application - Quick Start Guide

## For Your Manager: Simple One-Command Setup

### Prerequisites
- Docker Desktop installed and running
- Git (to clone the repository)

### Getting Started

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd entrust
   ```

2. **Start everything with one command**:
   ```bash
   docker-compose up
   ```

That's it! The system will automatically:
- Build all containers (postgres, backend, frontend)
- Deploy the database (tables, admin user, questions)
- Start all services

### Access the Application

Once containers are running:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000  
- **API Documentation**: http://localhost:8000/docs

### Default Login Credentials

- **User ID**: `admin`
- **Password**: `admin123`

⚠️ **Important**: Change the admin password in production!

### Stopping the Application

Press `Ctrl+C` in the terminal, or run:
```bash
docker-compose down
```

### Checking Status

To see if all containers are running:
```bash
docker-compose ps
```

All three services (postgres, backend, frontend) should show as "Up".

### Troubleshooting

If you encounter any issues:

1. **Check container logs**:
   ```bash
   docker-compose logs backend
   docker-compose logs frontend
   ```

2. **Rebuild containers** (if code changed):
   ```bash
   docker-compose up --build
   ```

3. **Reset everything** (fresh start):
   ```bash
   docker-compose down -v
   docker-compose up
   ```

### What Gets Deployed Automatically

- ✅ PostgreSQL database
- ✅ All database tables
- ✅ Default admin user
- ✅ 700 survey questions
- ✅ All database migrations
- ✅ Backend API server
- ✅ Frontend web application

No manual database setup required!

