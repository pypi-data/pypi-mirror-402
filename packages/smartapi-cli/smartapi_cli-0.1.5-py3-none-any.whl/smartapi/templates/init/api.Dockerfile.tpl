FROM python:3.11-slim

# Evita problemas de buffer e bytecode
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Diretório de trabalho
WORKDIR /app

# Dependências do sistema (psycopg2, etc)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements primeiro (cache de build)
COPY requirements.txt .

# Instala dependências (celery entra aqui)
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copia o código
COPY . .

# Comando default (API)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
