from pathlib import Path

def project_root() -> Path:
    return Path.cwd()

def app_path() -> Path:
    return project_root() / "app"

def modules_path() -> Path:
    return app_path() / "modules"

def jobs_path() -> Path:
    return app_path() / "jobs"
