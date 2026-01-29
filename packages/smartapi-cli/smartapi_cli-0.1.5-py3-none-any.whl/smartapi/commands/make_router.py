from __future__ import annotations

from pathlib import Path
import typer

from smartapi.utils.naming import to_snake
from smartapi.utils.project import modules_path
from smartapi.utils.templates import render_template

app = typer.Typer()


@app.command()
def make_router(module: str):
    """
    Cria o router.py dentro de um módulo existente
    """

    module_snake = to_snake(module)

    modules_base: Path = modules_path()
    module_path = modules_base / module_snake

    if not module_path.exists():
        typer.echo(f"❌ Módulo não existe: {module_path}")
        raise typer.Exit(1)

    router_path = module_path / "router.py"

    if router_path.exists():
        typer.echo(f"❌ Router já existe: {router_path}")
        raise typer.Exit(1)

    render_template(
        template="router/router.py.tpl",
        target=router_path,
        context={
            "module": module,
            "module_snake": module_snake,
        },
    )

    typer.echo(f"✅ Router criado em {router_path}")
