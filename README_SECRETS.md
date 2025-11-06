# Secrets Configuration

This project uses a separate `secrets.json` file to store API keys and credentials. This file is **not** committed to git for security reasons.

## Setup Instructions

1. **Copy the example file:**
   ```bash
   cp secrets.json.example secrets.json
   ```

2. **Edit `secrets.json` with your actual credentials:**
   ```json
   {
     "azure": {
       "endpoint": "https://your-azure-endpoint.openai.azure.com/",
       "api_key": "your-azure-api-key-here",
       "api_version": "2024-12-01-preview"
     },
     "aws": {
       "region": "us-east-1",
       "access_key_id": "your-aws-access-key-id",
       "secret_access_key": "your-aws-secret-access-key"
     }
   }
   ```

3. **When you run `docker-compose up`:**
   - The `load_secrets.py` script automatically runs
   - It reads `secrets.json` and generates `frontend/src/config/secrets.js`
   - The frontend uses these secrets to auto-fill credentials in the LLM Configuration UI

## Sending Secrets to Your Manager

1. **Send `secrets.json` separately** (via secure channel, not in git)
2. **Send `secrets.json.example`** as a template (this is safe to commit)
3. **Your manager should:**
   - Place `secrets.json` in the project root directory
   - Run `docker-compose up` as usual
   - The secrets will be automatically loaded

## Manual Execution

If you need to run the script manually:

```bash
python backend/load_secrets.py
```

This will generate `frontend/src/config/secrets.js` from `secrets.json`.

## Security Notes

- `secrets.json` is in `.gitignore` and will never be committed
- `frontend/src/config/secrets.js` is also in `.gitignore` (auto-generated)
- Never commit actual API keys or credentials to git
- Use secure channels (encrypted email, password manager, etc.) to share `secrets.json`

