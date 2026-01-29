from __future__ import annotations

from pathlib import Path
import typer

from smartapi.utils.naming import to_snake
from smartapi.utils.project import modules_path
from smartapi.utils.templates import render_template

app = typer.Typer()


@app.command()
def make_schema(module: str, name: str | None = None):
    """
    Cria um schema Pydantic dentro de um módulo existente
    """

    module_snake = to_snake(module)
    schema_name = name or module
    schema_snake = to_snake(schema_name)

    modules_base: Path = modules_path()
    module_path = modules_base / module_snake

    if not module_path.exists():
        typer.echo(f"❌ Módulo não existe: {module_path}")
        raise typer.Exit(1)

    schema_dir = module_path / "schemas"
    schema_dir.mkdir(parents=True, exist_ok=True)

    schema_path = schema_dir / f"{schema_snake}_schema.py"

    if schema_path.exists():
        typer.echo(f"❌ Schema já existe: {schema_path}")
        raise typer.Exit(1)

    render_template(
        template="schema/schema.py.tpl",
        target=schema_path,
        context={
            "schema": schema_name,
        },
    )

    typer.echo(f"✅ Schema '{schema_name}' criado em {schema_path}")
