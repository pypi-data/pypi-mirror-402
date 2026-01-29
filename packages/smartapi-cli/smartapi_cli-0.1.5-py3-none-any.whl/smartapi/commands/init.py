from __future__ import annotations

from pathlib import Path
import typer

from smartapi.utils.templates import render_template

app = typer.Typer()


@app.command()
def init_project():
    """
    Inicializa um projeto SmartAPI na pasta atual
    """

    root = Path.cwd()

    # --------------------
    # Proteções
    # --------------------
    if (root / "app").exists():
        typer.echo("❌ Projeto já inicializado (pasta 'app' existe).")
        raise typer.Exit(1)

    if (root / "pyproject.toml").exists():
        typer.echo("❌ Já existe um pyproject.toml neste diretório.")
        raise typer.Exit(1)

    typer.echo("🚀 Inicializando projeto SmartAPI...")

    # --------------------
    # Estrutura base
    # --------------------
    (root / "app/core/database").mkdir(parents=True, exist_ok=True)
    (root / "app/modules").mkdir(parents=True, exist_ok=True)
    (root / "app/jobs").mkdir(parents=True, exist_ok=True)
    (root / "app/shared").mkdir(parents=True, exist_ok=True)
    (root / "migrations/versions").mkdir(parents=True, exist_ok=True)
    (root / ".docker").mkdir(parents=True, exist_ok=True)

    # --------------------
    # __init__.py
    # --------------------
    for p in [
        "app",
        "app/core",
        "app/core/database",
        "app/modules",
        "app/jobs",
        "app/shared",
    ]:
        (root / p / "__init__.py").touch()

    # --------------------
    # Core / App
    # --------------------
    render_template(
        template="init/main.py.tpl",
        target=root / "app/main.py",
        context={},
    )

    render_template(
        template="init/worker.py.tpl",
        target=root / "app/worker.py",
        context={},
    )

    render_template(
        template="init/config.py.tpl",
        target=root / "app/core/config.py",
        context={},
    )

    render_template(
        template="init/security.py.tpl",
        target=root / "app/core/security.py",
        context={},
    )

    render_template(
        template="init/celery_app.py.tpl",
        target=root / "app/core/celery_app.py",
        context={},
    )

    render_template(
        template="init/controller.py.tpl",
        target=root / "app/shared/controller.py",
        context={},
    )

    # --------------------
    # Database (PASTA)
    # --------------------
    render_template(
        template="init/async_db.py.tpl",
        target=root / "app/core/database/async_db.py",
        context={},
    )

    render_template(
        template="init/sync_db.py.tpl",
        target=root / "app/core/database/sync_db.py",
        context={},
    )

    render_template(
        template="init/models.py.tpl",
        target=root / "app/core/database/models.py",
        context={},
    )

    # --------------------
    # Docker
    # --------------------
    render_template(
        template="init/docker-compose.yml.tpl",
        target=root / "docker-compose.yml",
        context={},
    )

    render_template(
        template="init/api.Dockerfile.tpl",
        target=root / ".docker/api.Dockerfile",
        context={},
    )

    # --------------------
    # Configs raiz
    # --------------------
    render_template(
        template="init/.env.tpl",
        target=root / ".env",
        context={},
    )
    
    render_template(
        template="init/requirements.txt.tpl",
        target=root / "requirements.txt",
        context={},
    )

    render_template(
        template="init/.env.example.tpl",
        target=root / ".env.example",
        context={},
    )

    render_template(
        template="init/gitignore.tpl",
        target=root / ".gitignore",
        context={},
    )

    render_template(
        template="init/alembic.ini.tpl",
        target=root / "alembic.ini",
        context={},
    )

    render_template(
        template="init/README.md.tpl",
        target=root / "README.md",
        context={},
    )

    typer.echo("")
    typer.echo("✅ Projeto SmartAPI inicializado com sucesso!")
    typer.echo("")
    typer.echo("👉 Próximos passos:")
    typer.echo("   docker compose up")
    typer.echo("   smartapi make:module User")
