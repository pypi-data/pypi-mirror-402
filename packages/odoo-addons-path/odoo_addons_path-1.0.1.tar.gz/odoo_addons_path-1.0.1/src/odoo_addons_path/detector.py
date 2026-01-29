from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

import yaml


class CodeBaseDetector(ABC):
    _next_detector: Optional["CodeBaseDetector"] = None

    def set_next(self, detector: "CodeBaseDetector") -> "CodeBaseDetector":
        self._next_detector = detector
        return detector

    @abstractmethod
    def detect(self, codebase: Path) -> tuple[str, dict[str, Any]] | None:
        if self._next_detector:
            return self._next_detector.detect(codebase)
        return None


class TrobzDetector(CodeBaseDetector):
    def detect(self, codebase: Path) -> tuple[str, dict[str, Any]] | None:
        if (codebase / ".trobz").is_dir():
            addons_dirs = []
            for item in (codebase / "addons").iterdir():
                if item.is_dir():
                    addons_dirs.append(item)
            return (
                "Trobz",
                {
                    "addons_dirs": addons_dirs,
                    "addons_dir": [codebase / "project"],
                    "odoo_dir": [
                        codebase / "odoo/addons",
                        codebase / "odoo/odoo/addons",
                    ],
                },
            )
        return super().detect(codebase)


class DoodbaDetector(CodeBaseDetector):
    """
    ┌─ root/
    │  └── odoo/
    │      └── custom/
    │          └── src/
    │              ├── odoo/         # Odoo core addons
    │              │   └── addons/
    │              ├── private/
    │              │   └── addon4/
    │              └── submodule/
    │                  └── addon1/
    """

    def detect(self, codebase: Path) -> tuple[str, dict[str, Any]] | None:
        copier_answers_file = codebase / ".copier-answers.yml"
        if not copier_answers_file.is_file():
            return super().detect(codebase)
        with open(copier_answers_file) as f:
            try:
                answers = yaml.safe_load(f)
                if "doodba" in answers.get("_src_path", ""):
                    addons_dirs = []
                    path = codebase / "odoo" / "custom" / "src"
                    if path.is_dir():
                        for item in path.iterdir():
                            if item.is_dir() and item.name not in ("odoo", "private"):
                                addons_dirs.append(item)
                        return (
                            "Doodba",
                            {
                                "addons_dirs": addons_dirs,
                                "addons_dir": [codebase / "odoo/custom/src/private"],
                                "odoo_dir": [
                                    codebase / "odoo/custom/src/odoo/addons",
                                    codebase / "odoo/custom/src/odoo/odoo/addons",
                                ],
                            },
                        )
            except yaml.YAMLError:
                pass
        return super().detect(codebase)


class C2CDetector(CodeBaseDetector):
    """
    Supports both legacy and new C2C project structures:

    Legacy Layout:
    ┌─ odoo/
    │  ├── Dockerfile
    │  ├── src/                # Odoo core source
    │  │   ├── addons/
    │  │   └── odoo/
    │  │       └── addons/
    │  ├── external-src/
    │  │   └── custom-repo/
    │  └── local-src/
    │      └── addon2/

    New Layout:
    ┌─ root/
    ├── Dockerfile
    ├── odoo/
    │  ├── addons/
    │  │   └── addon1/
    │  ├── dev-src/
    │  │   └── addon2/
    │  ├── paid-modules/
    │  │   └── addon3/
    │  └── external-src/
    │       ├── custom-repo/
    │       └── addon4/
    """

    def _find_docker_file(self, codebase: Path) -> Path | None:
        for path in [codebase / "odoo" / "Dockerfile", codebase / "Dockerfile"]:
            if path.is_file():
                return path
        return None

    def _is_c2c_dockerfile(self, docker_file: Path) -> bool:
        try:
            with open(docker_file) as f:
                content = f.read()
                return "LABEL maintainer='Camptocamp'" in content or 'LABEL maintainer="Camptocamp"' in content
        except (FileNotFoundError, PermissionError, OSError):
            return False

    def _collect_external_src_dirs(self, codebase: Path) -> list[Path]:
        addons_dirs = []
        external_src_dir = codebase / "odoo" / "external-src"
        if external_src_dir.is_dir():
            for item in external_src_dir.iterdir():
                if item.is_dir():
                    addons_dirs.append(item)
        return addons_dirs

    def _detect_legacy_layout(self, codebase: Path) -> bool:
        odoo_src_dir = codebase / "odoo" / "src"
        return odoo_src_dir.is_dir()

    def _get_legacy_config(self, codebase: Path, addons_dirs: list[Path]) -> dict[str, Any]:
        return {
            "addons_dirs": addons_dirs,
            "addons_dir": [codebase / "odoo/local-src"],
            "odoo_dir": [
                codebase / "odoo/src/addons",
                codebase / "odoo/src/odoo/addons",
            ],
        }

    def _get_new_config(self, codebase: Path, addons_dirs: list[Path]) -> dict[str, Any]:
        addons_dir_paths = []
        odoo_dir_paths = []

        for dir_name in ["dev-src", "paid-modules"]:
            dir_path = codebase / "odoo" / dir_name
            if dir_path.is_dir():
                addons_dir_paths.append(dir_path)

        odoo_addons_dir = codebase / "odoo" / "addons"
        if odoo_addons_dir.is_dir():
            odoo_dir_paths.append(odoo_addons_dir)

        return {
            "addons_dirs": addons_dirs,
            "addons_dir": addons_dir_paths,
            "odoo_dir": odoo_dir_paths,
        }

    def detect(self, codebase: Path) -> tuple[str, dict[str, Any]] | None:
        docker_file = self._find_docker_file(codebase)
        if not docker_file or not self._is_c2c_dockerfile(docker_file):
            return super().detect(codebase)

        addons_dirs = self._collect_external_src_dirs(codebase)

        if self._detect_legacy_layout(codebase):
            return "Camptocamp (Legacy)", self._get_legacy_config(codebase, addons_dirs)
        else:
            return "Camptocamp", self._get_new_config(codebase, addons_dirs)


class OdooShDetector(CodeBaseDetector):
    """
    Follow Odoo.sh mode
    src/
    ├── enterprise/         # Odoo Enterprise
    ├── odoo/               # Odoo core
    └── themes/
    ├── user/               # user's submodule
    │   └── OCA/
    """

    def detect(self, codebase: Path) -> tuple[str, dict[str, Any]] | None:
        if (
            (codebase / "enterprise").is_dir()
            and (codebase / "odoo").is_dir()
            and (codebase / "themes").is_dir()
            and (codebase / "user").is_dir()
        ):
            addons_dirs = [codebase / "enterprise", codebase / "themes"]
            for item in (codebase / "user").iterdir():
                if item.is_dir():
                    addons_dirs.append(item)
            return (
                "odoo.sh",
                {
                    "addons_dirs": addons_dirs,
                    "addons_dir": [codebase / "project"],
                    "odoo_dir": [
                        codebase / "odoo/addons",
                        codebase / "odoo/odoo/addons",
                    ],
                },
            )
        return super().detect(codebase)


class GenericDetector(CodeBaseDetector):
    """
    A fallback detector that looks for any folder that contains __manifest__.py
    """

    def detect(self, codebase: Path) -> tuple[str, dict[str, Any]] | None:
        manifest_files = []
        for manifest_file in codebase.glob("**/__manifest__.py"):
            # ignore setup folder in a module
            if "setup" in manifest_file.parts:
                continue
            # ignore folder in a same folder
            str_manifest_file = str(manifest_file)
            if str_manifest_file.count("__manifest__.py") > 1:
                continue
            manifest_files.append(str_manifest_file)
        if not manifest_files:
            return super().detect(codebase)

        addons_dirs = set()
        for manifest_file in manifest_files:
            addons_dirs.add(Path(manifest_file).parent.parent)

        return "fallback", {"addons_dirs": list(addons_dirs)}
