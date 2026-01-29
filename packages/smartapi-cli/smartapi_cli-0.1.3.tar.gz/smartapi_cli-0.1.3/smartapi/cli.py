import typer

from smartapi.commands import (
    make_module,
    make_controller,
    make_service,
    make_model,
    make_schema,
    make_router,
    make_crud,
    make_job,
    make_migration,
    app_run,
    db_migrate,
    db_rollback,
    init
)

app = typer.Typer(help="SmartAPI – Opinionated FastAPI CLI")

app.command("make:module")(make_module.make_module)
app.command("make:controller")(make_controller.make_controller)
app.command("make:service")(make_service.make_service)
app.command("make:model")(make_model.make_model)
app.command("make:schema")(make_schema.make_schema)
app.command("make:router")(make_router.make_router)
app.command("make:crud")(make_crud.make_crud)
app.command("make:job")(make_job.make_job)
app.command("make:migration")(make_migration.make_migration)

app.command("db:migrate")(db_migrate.db_migrate)
app.command("db:rollback")(db_rollback.db_rollback)

app.add_typer(app_run.app, name="app")
app.command("init")(init.init_project)

def main():
    app()

if __name__ == "__main__":
    main()
