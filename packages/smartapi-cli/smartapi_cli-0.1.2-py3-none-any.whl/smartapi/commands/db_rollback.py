from __future__ import annotations

import subprocess
from pathlib import Path
import typer

app = typer.Typer()


@app.command()
def db_rollback(steps: int = 1):
    """
    Executa rollback de migrations (default: 1)
    """

    alembic_ini = Path("alembic.ini")

    if not alembic_ini.exists():
        typer.echo("❌ alembic.ini não encontrado na raiz do projeto")
        raise typer.Exit(1)

    typer.echo(f"⏪ Revertendo {steps} migration(s)")

    try:
        subprocess.run(
            ["alembic", "downgrade", f"-{steps}"],
            check=True,
        )
    except subprocess.CalledProcessError:
        typer.echo("❌ Erro ao executar rollback")
        raise typer.Exit(1)

    typer.echo("✅ Rollback executado com sucesso")
