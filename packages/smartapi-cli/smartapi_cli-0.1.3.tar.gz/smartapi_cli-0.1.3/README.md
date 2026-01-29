# 🚀 SmartAPI

SmartAPI é um **CLI opinativo** para criação de APIs modernas e escaláveis com **FastAPI**.  
Ele gera uma API completa **do zero**, já arquitetada, padronizada e pronta para produção.

---

## ✨ O que o SmartAPI entrega

- FastAPI + Uvicorn
- Celery + Redis
- PostgreSQL
- SQLAlchemy + Alembic
- Configuração de ambientes (.env)
- Docker + Docker Compose
- Padrão de módulos, controllers, services e jobs
- CLI para geração de código e automação de tarefas

---

## 📦 Instalação

```bash
pip install smartapi
```

---

## ⚡ Criando um projeto

Inicializando um projeto na pasta atual:

```bash
smartapi init

docker compose up --build -d
```

A API ficará disponível em:

```
http://localhost:8000
```

---

## 📚 Documentação automática

FastAPI gera documentação automaticamente:

- Swagger UI  
  http://localhost:8000/docs

- ReDoc  
  http://localhost:8000/redoc

---

## 🧱 Estrutura do projeto

```text
app/
├── core/                Configurações centrais (app, db, celery, env)
├── modules/             Módulos da aplicação
│   └── example/
│       ├── controller/
│       ├── service/
│       ├── model/
│       ├── schemas/
│       └── router.py
├── jobs/                Jobs Celery
└── main.py              Entry point FastAPI

alembic/                 Migrations
docker/                  Dockerfiles
docker-compose.yml
requirements.txt
.env.example
```

---

## 🧩 Comandos disponíveis

```bash
smartapi make:module <Module>
smartapi make:controller <Module>
smartapi make:service <Module>
smartapi make:model <Module>
smartapi make:schema <Module>
smartapi make:router <Module>
smartapi make:crud
smartapi make:job
smartapi make:migration
```

### Banco de dados

```bash
smartapi db:migrate
smartapi db:rollback
```

### Executar a aplicação

```bash
smartapi app run
```

---

## 🧠 Filosofia

- Convenção > configuração
- Código previsível
- Arquitetura modular
- Infra pronta desde o dia 0
- Menos boilerplate, mais produto

---

## 📄 Licença

MIT

Criado com ❤️ por **Arthur Rezende**