version: "3.9"

services:
  api:
    build:
      context: .
      dockerfile: .docker/api.Dockerfile
    env_file:
      - .env
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis

  worker:
    build:
      context: .
      dockerfile: .docker/api.Dockerfile
    command: celery -A app.worker worker -l info
    env_file:
      - .env
    volumes:
      - .:/app
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: app_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7
    ports:
      - "6379:6379"
    
  flower:
    image: mher/flower
    command: celery --broker=redis://redis:6379/0 flower
    ports:
      - "5555:5555"
    depends_on:
      - redis

volumes:
  pgdata:
