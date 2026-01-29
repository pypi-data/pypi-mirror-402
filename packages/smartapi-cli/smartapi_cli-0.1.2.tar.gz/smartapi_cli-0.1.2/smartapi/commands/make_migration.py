from __future__ import annotations

import subprocess
from pathlib import Path
import typer

app = typer.Typer()

def make_migration(message: str):
    subprocess.run(["alembic", "revision", "--autogenerate", "-m", message])