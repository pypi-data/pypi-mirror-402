import glob
from pathlib import Path
from typing import Annotated

import typer

from .main import get_addons_path


def _parse_paths(values: list[str] | None) -> list[Path]:
    if not values:
        return []
    paths: list[Path] = []
    for value in values:
        for p_str in value.split(","):
            p_str = p_str.strip()
            if not p_str:
                continue
            p = Path(p_str).expanduser()
            if "*" in str(p) or "?" in str(p) or "[" in str(p):
                paths.extend(Path(g) for g in sorted(glob.glob(str(p), recursive=True)))
            else:
                paths.append(p)
    return paths


app = typer.Typer()


@app.command()
def main(
    codebase: Annotated[
        Path,
        typer.Argument(
            envvar="CODEBASE",
            help="Path to the Odoo project. Can also be set via the CODEBASE environment variable.",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = Path("./"),
    addons_dir: Annotated[
        list[str] | None,
        typer.Option(
            help=(
                "Paths that are addon directories (contain Odoo modules) or "
                "paths that contain addon directories (repositories with multiple Odoo modules). "
                "Globs and comma-separated values are supported."
            ),
        ),
    ] = None,
    odoo_dir: Annotated[
        str | None,
        typer.Option(
            help="Path containing the Odoo source code.",
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
        ),
    ] = False,
):
    """
    Return addons_path constructor
    """
    odoo_dir_path = None
    if odoo_dir:
        odoo_dir_path = Path(odoo_dir).expanduser()
        if not odoo_dir_path.exists():
            typer.secho(f"Odoo dir {odoo_dir} not found.", fg=typer.colors.RED)
            raise typer.Exit(1)

    paths = _parse_paths(addons_dir)

    addons_path = get_addons_path(
        codebase=codebase,
        addons_dir=paths,
        odoo_dir=odoo_dir_path,
        verbose=verbose,
    )

    if not verbose:
        typer.echo(addons_path)
