# Database Deployment Helper Script (PowerShell)
# Usage: .\deploy.ps1 [init-only|migrate-only|migrate <name>|full]

param(
    [Parameter(Position=0)]
    [ValidateSet("init-only", "migrate-only", "migrate", "full")]
    [string]$Action = "full",
    
    [Parameter(Position=1)]
    [ValidateSet("password", "llm_model", "llm_providers", "questions_fields", "user_submissions")]
    [string]$MigrationName
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "EnTrust Database Deployment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check if database URL is set
if (-not $env:DATABASE_URL) {
    Write-Host "Warning: DATABASE_URL environment variable not set" -ForegroundColor Yellow
    Write-Host "Using default: postgresql://entrust_user:entrust_pass@localhost:5432/entrust_db" -ForegroundColor Yellow
    Write-Host ""
}

# Run deployment based on action
switch ($Action) {
    "init-only" {
        Write-Host "Running database initialization only..." -ForegroundColor Yellow
        python deploy_db.py --init-only
    }
    "migrate-only" {
        Write-Host "Running migrations only..." -ForegroundColor Yellow
        python deploy_db.py --migrate-only
    }
    "migrate" {
        if (-not $MigrationName) {
            Write-Host "Error: Migration name required" -ForegroundColor Red
            Write-Host "Usage: .\deploy.ps1 migrate <migration_name>" -ForegroundColor Yellow
            Write-Host "Available migrations: password, llm_model, llm_providers, questions_fields, user_submissions" -ForegroundColor Yellow
            exit 1
        }
        Write-Host "Running migration: $MigrationName" -ForegroundColor Yellow
        python deploy_db.py --migrate $MigrationName
    }
    "full" {
        Write-Host "Running full deployment (init + migrations)..." -ForegroundColor Yellow
        python deploy_db.py
    }
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Deployment completed!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

