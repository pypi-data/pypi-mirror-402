import typer
import subprocess

app = typer.Typer(help="Executa a aplicação FastAPI")

@app.command("run")
def app_run(
    host: str = typer.Option("0.0.0.0", help="Host da aplicação"),
    port: int = typer.Option(8000, help="Porta da aplicação"),
    reload: bool = typer.Option(True, help="Ativa reload automático"),
    workers: int | None = typer.Option(None, help="Número de workers"),
):
    """
    Executa a aplicação FastAPI usando Uvicorn
    """

    cmd = [
        "uvicorn",
        "app.main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]

    if reload:
        cmd.append("--reload")

    if workers:
        cmd.extend(["--workers", str(workers)])

    typer.echo(f"🚀 API rodando em http://{host}:{port}")
    subprocess.run(cmd)
