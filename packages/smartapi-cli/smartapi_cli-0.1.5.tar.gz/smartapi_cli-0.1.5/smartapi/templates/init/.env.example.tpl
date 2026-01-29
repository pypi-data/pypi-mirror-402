APP_NAME=SmartAPI
ENV=local

DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/app_db
DATABASE_URL_SYNC=postgresql+psycopg2://postgres:postgres@db:5432/app_db

REDIS_URL=redis://redis:6379/0

JWT_SECRET=changeme
JWT_EXPIRES_IN=3600
