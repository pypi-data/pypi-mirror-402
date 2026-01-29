from pathlib import Path

import typer

from odoo_addons_path.detector import C2CDetector, DoodbaDetector, GenericDetector, OdooShDetector, TrobzDetector


def _add_to_path(path_list: list[str], dirs_to_add: list[Path], is_sorted: bool = False):
    if is_sorted:
        dirs_to_add = sorted(dirs_to_add, key=lambda p: p.name)
    for d in dirs_to_add:
        if d.is_dir():
            resolved_path = str(d.resolve())
            if resolved_path not in path_list:
                path_list.append(resolved_path)


def _detect_codebase_layout(codebase: Path, verbose: bool = False) -> dict:
    trobz = TrobzDetector()
    c2c = C2CDetector()
    odoo_sh = OdooShDetector()
    doodba = DoodbaDetector()
    fallback = GenericDetector()
    trobz.set_next(c2c).set_next(odoo_sh).set_next(doodba).set_next(fallback)
    res = trobz.detect(codebase)
    if not res:
        typer.secho("No codebase layout detected", fg=typer.colors.RED)
        raise typer.Exit(1)
    detector_name, detected_paths = res
    if verbose:
        typer.echo(f"Codebase layout: {detector_name}")
    return detected_paths


def _process_paths(
    all_paths: dict[str, list[str]],
    detected_paths: dict,
    addons_dir: list[Path] | None,
    odoo_dir: Path | None,
):
    if odoo_dir:
        _add_to_path(
            all_paths["odoo_dir"],
            [odoo_dir / "addons", odoo_dir / "odoo" / "addons"],
        )
    if detected_paths.get("odoo_dir"):
        _add_to_path(all_paths["odoo_dir"], detected_paths["odoo_dir"])

    all_addon_paths_to_process = (
        (addons_dir or []) + detected_paths.get("addons_dirs", []) + detected_paths.get("addons_dir", [])
    )

    result = []

    for p in all_addon_paths_to_process:
        if not p.is_dir():
            continue
        manifests = p.glob("**/__manifest__.py")
        for manifest in sorted(manifests):
            repo_path = manifest.parent.parent
            if repo_path not in result:
                result.append(repo_path)

    _add_to_path(
        all_paths["addon_repositories"],
        result,
        is_sorted=not bool(addons_dir),
    )


def get_addons_path(
    codebase: Path,
    addons_dir: list[Path] | None = None,
    odoo_dir: Path | None = None,
    verbose: bool = False,
) -> str:
    all_paths: dict[str, list[str]] = {
        "odoo_dir": [],
        "addon_repositories": [],
    }

    detected_paths = {}
    # Skip detector only if both paths are None (no explicit paths provided)
    if not addons_dir and not odoo_dir:
        detected_paths = _detect_codebase_layout(codebase, verbose)

    _process_paths(all_paths, detected_paths, addons_dir, odoo_dir)

    result = [path for paths in all_paths.values() for path in paths]
    addons_path = ",".join(result)

    if verbose:
        for category, paths in all_paths.items():
            if paths:
                typer.echo(f"\n# {category}")
                for path in paths:
                    typer.echo(path)
        typer.echo("\n# addons_path")
        typer.echo(addons_path)

    return addons_path
