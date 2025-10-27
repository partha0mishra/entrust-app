-- SQL script to update admin password to 'Welcome123!'
-- Run this with: psql -U entrust_user -d entrust_db -f update_admin_password.sql

-- The password hash for 'Welcome123!' using bcrypt
-- You'll need to replace HASHED_PASSWORD_HERE with the actual hash

-- For reference, here's what you need to do:
-- 1. Install dependencies: pip install passlib bcrypt
-- 2. Run Python to generate hash:
--    python -c "from passlib.context import CryptContext; pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto'); print(pwd_context.hash('Welcome123!'))"
-- 3. Replace HASHED_PASSWORD_HERE below with the output

UPDATE users
SET password_hash = 'HASHED_PASSWORD_HERE'
WHERE user_id = 'admin';

-- Verify the update
SELECT user_id, username, user_type
FROM users
WHERE user_id = 'admin';
