from __future__ import annotations
from pathlib import Path


def render_template(
    *,
    template: str,
    target: Path,
    context: dict,
):
    templates_base = Path(__file__).resolve().parent.parent / "templates"
    template_path = templates_base / template

    if not template_path.exists():
        raise FileNotFoundError(f"Template não encontrado: {template_path}")

    content = template_path.read_text(encoding="utf-8")

    if context:
        try:
            rendered = content.format(**context)
        except KeyError as e:
            raise KeyError(
                f"Variável {e} não encontrada no contexto do template {template}"
            )
    else:
        rendered = content

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(rendered, encoding="utf-8")
