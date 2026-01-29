from pathlib import Path
from builders_hut.setups.base_setup import BaseSetup
import platform
import tomlkit
import subprocess


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


def make_folder(loc: Path):
    """make a folder in the given path"""
    loc.mkdir(exist_ok=True, parents=True)


def make_file(file: Path):
    """make a file in the given location"""
    file.touch(exist_ok=True)


def write_file(path: Path, content: str) -> None:
    """write data to a file"""
    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist")

    path.write_text(content, encoding="utf-8")


def run_subprocess(location: Path, command: str):
    """
    Run subprocess command
    """
    subprocess.run(
        command,
        cwd=location,
        shell=True,
        check=True,
        stderr=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
    )
