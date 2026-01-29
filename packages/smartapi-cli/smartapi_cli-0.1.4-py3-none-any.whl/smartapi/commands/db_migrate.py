from __future__ import annotations

import subprocess
from pathlib import Path
import typer

app = typer.Typer()


@app.command()
def db_migrate():
    """
    Executa alembic upgrade head
    """

    alembic_ini = Path("alembic.ini")

    if not alembic_ini.exists():
        typer.echo("❌ alembic.ini não encontrado na raiz do projeto")
        raise typer.Exit(1)

    typer.echo("🚀 Aplicando migrations (alembic upgrade head)")

    try:
        subprocess.run(
            ["alembic", "upgrade", "head"],
            check=True,
        )
    except subprocess.CalledProcessError:
        typer.echo("❌ Erro ao executar migrations")
        raise typer.Exit(1)

    typer.echo("✅ Banco atualizado com sucesso")
