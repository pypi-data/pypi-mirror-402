from __future__ import annotations

from pathlib import Path
import typer

from smartapi.utils.naming import to_snake
from smartapi.utils.project import modules_path
from smartapi.utils.templates import render_template

app = typer.Typer()


@app.command()
def make_service(module: str, name: str | None = None):
    """
    Cria um service dentro de um módulo existente
    """

    module_snake = to_snake(module)
    service_name = name or module
    service_snake = to_snake(service_name)

    modules_base: Path = modules_path()
    module_path = modules_base / module_snake

    if not module_path.exists():
        typer.echo(f"❌ Módulo não existe: {module_path}")
        raise typer.Exit(1)

    service_dir = module_path / "service"
    service_dir.mkdir(parents=True, exist_ok=True)

    service_path = service_dir / f"{service_snake}_service.py"

    if service_path.exists():
        typer.echo(f"❌ Service já existe: {service_path}")
        raise typer.Exit(1)

    render_template(
        template="service/service.py.tpl",
        target=service_path,
        context={
            "class_name": f"{service_name}Service",
        },
    )

    typer.echo(f"✅ Service '{service_name}Service' criado em {service_path}")
