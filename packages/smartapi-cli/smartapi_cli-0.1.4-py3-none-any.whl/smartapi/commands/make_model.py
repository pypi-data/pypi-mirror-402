from __future__ import annotations

from pathlib import Path
import typer

from smartapi.utils.naming import to_snake
from smartapi.utils.project import modules_path
from smartapi.utils.templates import render_template

app = typer.Typer()


@app.command()
def make_model(module: str, name: str):
    """
    Cria um model SQLAlchemy dentro de um módulo existente
    """

    module_snake = to_snake(module)
    model_snake = to_snake(name)

    modules_base: Path = modules_path()  # normalmente app/modules
    module_path = modules_base / module_snake

    if not module_path.exists():
        typer.echo(f"❌ Módulo não existe: {module_path}")
        raise typer.Exit(1)

    model_dir = module_path / "model"
    model_dir.mkdir(parents=True, exist_ok=True)

    model_path = model_dir / f"{model_snake}_model.py"

    if model_path.exists():
        typer.echo(f"❌ Model já existe: {model_path}")
        raise typer.Exit(1)

    render_template(
        template="model/model.py.tpl",
        target=model_path,
        context={
            "class_name": name,
            "table_name": f"{model_snake}s",
        },
    )

    typer.echo(f"✅ Model '{name}' criado em {model_path}")
