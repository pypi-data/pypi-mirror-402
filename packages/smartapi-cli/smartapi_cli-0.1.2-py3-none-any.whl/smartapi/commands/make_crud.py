from __future__ import annotations

import typer
from pathlib import Path

from smartapi.utils.naming import to_snake
from smartapi.utils.templates import render_template

app = typer.Typer()

BASE_MODULES = Path("app/modules")


@app.command()
def make_crud(
    module: str,
    entity: str,
    from_model: bool = typer.Option(False, "--from-model"),
    controller: str = typer.Option(None, "--controller"),
    readonly: bool = typer.Option(False, "--readonly"),
    no_delete: bool = typer.Option(False, "--no-delete"),
):
    module_snake = to_snake(module)
    entity_snake = to_snake(entity)

    module_path = BASE_MODULES / module_snake
    module_path.mkdir(parents=True, exist_ok=True)

    model_path = module_path / "model" / f"{entity_snake}_model.py"
    schema_path = module_path / "schemas" / f"{entity_snake}_schema.py"
    service_path = module_path / "service" / f"{entity_snake}_service.py"

    controller_name = controller or entity
    controller_snake = to_snake(controller_name)
    controller_path = module_path / "controller" / f"{controller_snake}_controller.py"

    router_path = module_path / "router.py"

    # -------------------------
    # MODEL
    # -------------------------
    if not from_model and not model_path.exists():
        render_template(
            template="crud/model.py.tpl",
            target=model_path,
            context={
                "entity": entity,
                "entity_snake": entity_snake,
            },
        )

    # -------------------------
    # SCHEMA
    # -------------------------
    render_template(
        template="crud/schema.py.tpl",
        target=schema_path,
        context={
            "entity": entity,
        },
    )

    # -------------------------
    # SERVICE
    # -------------------------
    render_template(
        template="crud/service.py.tpl",
        target=service_path,
        context={
            "entity": entity,
            "entity_snake": entity_snake,
            "module_snake": module_snake,
        },
    )

    # -------------------------
    # CONTROLLER BASE
    # -------------------------
    if not controller_path.exists():
        render_template(
            template="crud/controller.base.py.tpl",
            target=controller_path,
            context={
                "controller_name": controller_name,
                "entity": entity,
                "entity_snake": entity_snake,
                "module_snake": module_snake,
            },
        )

    # -------------------------
    # CONTROLLER METHODS (append)
    # -------------------------
    with open(controller_path, "a", encoding="utf-8") as f:
        from smartapi.utils.templates import render_template as _rt  # só pra gerar string

        tmp = Path("/tmp/_controller_methods.py")

        render_template(
            template="crud/controller.methods.py.tpl",
            target=tmp,
            context={
                "entity_snake": entity_snake,
            },
        )
        f.write(tmp.read_text())

        if not readonly:
            render_template(
                template="crud/controller.methods.delete.py.tpl",
                target=tmp,
                context={
                    "entity_snake": entity_snake,
                },
            )
            f.write(tmp.read_text())

    # -------------------------
    # ROUTER (append)
    # -------------------------
    with open(router_path, "a", encoding="utf-8") as f:
        tmp = Path("/tmp/_router_routes.py")

        render_template(
            template="crud/router.routes.py.tpl",
            target=tmp,
            context={
                "entity": entity,
                "entity_snake": entity_snake,
            },
        )
        f.write(tmp.read_text())

        if not readonly and not no_delete:
            render_template(
                template="crud/router.routes.delete.py.tpl",
                target=tmp,
                context={
                    "entity_snake": entity_snake,
                },
            )
            f.write(tmp.read_text())

    typer.echo(f"✅ CRUD '{entity}' criado no módulo '{module}'")
