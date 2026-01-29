import shutil
from pathlib import Path

import pytest

from odoo_addons_path.main import get_addons_path


@pytest.fixture
def base_dir(tmp_path: Path) -> Path:
    d = tmp_path / "project"
    d.mkdir()
    return d


@pytest.mark.parametrize(
    "layout, expected_paths",
    [
        (
            "trobz",
            [
                "odoo/addons",
                "odoo/odoo/addons",
                "addons/custom-repo",
                "project",
            ],
        ),
        (
            "c2c",
            [
                "odoo/src/addons",
                "odoo/src/odoo/addons",
                "odoo/external-src/custom-repo",
                "odoo/local-src",
            ],
        ),
        (
            "c2c-new",
            [
                "odoo/addons",
                "odoo/external-src/custom-repo",
                "odoo/dev-src",
                "odoo/paid-modules",
            ],
        ),
        (
            "doodba",
            [
                "odoo/custom/src/odoo/addons",
                "odoo/custom/src/odoo/odoo/addons",
                "odoo/custom/src/custom-repo",
                "odoo/custom/src/private",
            ],
        ),
        (
            "odoo-sh",
            [
                "odoo/addons",
                "odoo/odoo/addons",
                "enterprise",
                "user/local-src",
                "themes",
            ],
        ),
    ],
)
def test_layouts(base_dir: Path, layout: str, expected_paths: list[str]):
    shutil.copytree(Path(__file__).parent / "data" / layout, base_dir, dirs_exist_ok=True)
    expected_paths = [str((base_dir / path).resolve()) for path in expected_paths]
    expected_addons_path = ",".join(expected_paths)

    result = get_addons_path(base_dir)

    assert result == expected_addons_path
