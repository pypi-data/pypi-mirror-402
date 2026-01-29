# 🚀 API – Projeto FastAPI

Este projeto foi gerado automaticamente pelo **SmartAPI CLI**.  
Ele fornece uma base sólida, padronizada e pronta para produção utilizando **FastAPI**, **Celery** e **Docker**.
---

## Stack utilizada

- FastAPI + Uvicorn
- Celery + Redis
- PostgreSQL
- SQLAlchemy + Alembic
- Configuração de ambientes (.env)
- Docker + Docker Compose
- Padrão de módulos, controllers, services e jobs
- CLI para geração de código e automação de tarefas

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