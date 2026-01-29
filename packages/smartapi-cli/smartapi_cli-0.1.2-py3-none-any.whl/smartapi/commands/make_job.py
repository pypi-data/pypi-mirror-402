from __future__ import annotations

from pathlib import Path
import typer

from smartapi.utils.naming import to_snake
from smartapi.utils.project import jobs_path
from smartapi.utils.templates import render_template

app = typer.Typer()


@app.command()
def make_job(group: str, name: str):
    """
    Cria um job Celery padronizado e registra no app/jobs/__init__.py
    """

    group_snake = to_snake(group)
    job_snake = to_snake(name)

    jobs_base: Path = jobs_path()  # normalmente: Path("app/jobs")
    jobs_base.mkdir(parents=True, exist_ok=True)

    # registry principal (app/jobs/__init__.py)
    main_init = jobs_base / "__init__.py"
    if not main_init.exists():
        main_init.write_text("# jobs registry (auto-generated)\n", encoding="utf-8")

    # pasta do grupo
    group_path = jobs_base / group_snake
    group_path.mkdir(parents=True, exist_ok=True)

    # opcional, mas ok manter (app/jobs/<group>/__init__.py)
    (group_path / "__init__.py").touch(exist_ok=True)

    # arquivo do job
    job_path = group_path / f"{job_snake}.py"
    if job_path.exists():
        typer.echo(f"❌ Job já existe: {job_path}")
        raise typer.Exit(1)

    # gera conteúdo via template
    render_template(
        template="jobs/job.py.tpl",
        target=job_path,
        context={
            "group_snake": group_snake,
            "job_snake": job_snake,
            "job_display_name": name,
        },
    )

    # registra import no app/jobs/__init__.py (SEM duplicar)
    import_line = f"import app.jobs.{group_snake}.{job_snake}\n"
    current = main_init.read_text(encoding="utf-8")

    # evita duplicação (aceita com/sem newline anterior)
    if f"import app.jobs.{group_snake}.{job_snake}" not in current:
        with open(main_init, "a", encoding="utf-8") as f:
            # garante quebra antes se o arquivo não termina com newline
            if current and not current.endswith("\n"):
                f.write("\n")
            f.write(import_line)

    typer.echo(f"✅ Job '{name}' criado em {job_path} e registrado em app/jobs/__init__.py")
