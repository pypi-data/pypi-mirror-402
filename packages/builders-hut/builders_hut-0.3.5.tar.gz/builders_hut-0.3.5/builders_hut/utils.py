from pathlib import Path
from builders_hut.setups.base_setup import BaseSetup
import platform
import tomlkit


def write_pyproject(
    path: str | Path = "pyproject.toml",
    *,
    name: str,
    version: str = "0.1.0",
    description: str = "",
    python: str = ">=3.13",
    dependencies: list[str] | None = None,
    dev_dependencies: list[str] | None = None,
) -> None:
    """
    Completely write a pyproject.toml file.

    This function OVERWRITES any existing file.
    Intended for scaffolding / project initialization.
    """

    path = Path(path)
    doc = tomlkit.document()

    # ------------------
    # [project]
    # ------------------
    project = tomlkit.table()
    project.add("name", name)
    project.add("version", version)

    if description:
        project.add("description", description)

    project.add("requires-python", python)

    project.add(
        "dependencies",
        dependencies or [],
    )

    if dev_dependencies:
        optional = tomlkit.table()
        optional.add("dev", dev_dependencies)
        project.add("optional-dependencies", optional)

    # ------------------
    # [project.scripts]
    # ------------------
    scripts = tomlkit.table()
    scripts.add("run_dev_server", "app.scripts.dev:main")
    scripts.add("run_prod_server", "app.scripts.prod:main")
    project.add("scripts", scripts)

    doc.add("project", project)

    # Write file
    path.write_text(tomlkit.dumps(doc), encoding="utf-8")


def setup_project(location: Path, setup_cls: type[BaseSetup], **config) -> None:
    """
    Take BaseSetup and make the project
    """
    setup = setup_cls(location)
    setup.configure(**config)
    setup.create()


def get_platform():
    """check the operating system"""
    system = platform.system()
    return system.lower()
