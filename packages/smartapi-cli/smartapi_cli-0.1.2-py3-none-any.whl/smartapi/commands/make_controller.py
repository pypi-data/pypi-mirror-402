from __future__ import annotations

from pathlib import Path
import typer

from smartapi.utils.naming import to_snake
from smartapi.utils.project import modules_path
from smartapi.utils.templates import render_template

app = typer.Typer()


@app.command()
def make_controller(module: str, name: str | None = None):
    """
    Cria um controller dentro de um módulo existente
    """

    module_snake = to_snake(module)
    controller_name = name or module
    controller_snake = to_snake(controller_name)

    modules_base: Path = modules_path()
    module_path = modules_base / module_snake

    if not module_path.exists():
        typer.echo(f"❌ Módulo não existe: {module_path}")
        raise typer.Exit(1)

    controller_dir = module_path / "controller"
    controller_dir.mkdir(parents=True, exist_ok=True)

    controller_path = controller_dir / f"{controller_snake}_controller.py"

    if controller_path.exists():
        typer.echo(f"❌ Controller já existe: {controller_path}")
        raise typer.Exit(1)

    render_template(
        template="controller/controller.py.tpl",
        target=controller_path,
        context={
            "class_name": f"{controller_name}Controller",
        },
    )

    typer.echo(f"✅ Controller '{controller_name}Controller' criado em {controller_path}")
