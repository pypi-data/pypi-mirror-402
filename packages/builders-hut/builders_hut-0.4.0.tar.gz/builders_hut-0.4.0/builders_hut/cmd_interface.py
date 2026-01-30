from pathlib import Path

import typer
from rich.console import Console
from typing import Literal
from builders_hut.setups import (
    SetupEnv,
    SetupFiles,
    SetupFileWriter,
    SetupStructure,
    SetupDatabase,
    SetupGithub,
)
from builders_hut.utils import setup_project
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
)


console = Console()
app = typer.Typer(
    invoke_without_command=True,
    no_args_is_help=True,
)

BANNER = r"""
[bold cyan]
 ____        _ _     _                 _   _       _   
| __ ) _   _(_) | __| | ___ _ __ ___  | | | |_   _| |_ 
|  _ \| | | | | |/ _` |/ _ \ '__/ __| | |_| | | | | __|
| |_) | |_| | | | (_| |  __/ |  \__ \ |  _  | |_| | |_ 
|____/ \__,_|_|_|\__,_|\___|_|  |___/ |_| |_|\__,_|\__|
[/bold cyan]
"""

APP_VERSION = "0.4.0"


@app.callback()
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show the version and exit",
        is_eager=True,
    ),
):
    """Builders Hut – FastAPI Scaffolding Tool"""
    console.print(BANNER)

    if version:
        console.print(f"[bold green]hut version {APP_VERSION}[/bold green]")

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command()
def build(
    name: str = typer.Option(
        Path.cwd().name,
        "--name",
        "-n",
        help="Project name",
    ),
    description: str = typer.Option(
        "A new project",
        "--description",
        "-d",
        help="Project description",
    ),
    version: str = typer.Option(
        "0.1.0",
        "--version",
        "-v",
        help="Project version",
    ),
    path: Path = typer.Option(
        Path.cwd(),
        "--path",
        "-p",
        help="Project directory",
    ),
    database_type: Literal["sql", "nosql"] = typer.Option(
        "sql",
        "--database-type",
        "-dt",
        help="Database Type (sql, nosql)",
    ),
    database_provider: Literal["postgres", "mysql", "sqlite", "mongodb"] = typer.Option(
        "postgres",
        "--database-provider",
        "-dp",
        help="Database Provider (postgres, mysql, sqlite, mongodb)",
    ),
    accept_default: bool = typer.Option(
        None,
        "--accept_defaults",
        "-y",
        help="Run command with all default values selected",
    ),
):
    """
    Build project structure (CLI or interactive).
    """
    # ===== Defaults =====
    DEFAULTS = {
        "name": Path.cwd().name,
        "description": "A new project",
        "version": "0.1.0",
        "database_type": "sql",
        "database_provider": "postgres",
    }

    # ===== Apply defaults or prompt =====
    if accept_default:
        name = name or DEFAULTS["name"]
        description = description or DEFAULTS["description"]
        version = version or DEFAULTS["version"]
        database_type = database_type or DEFAULTS["database_type"]
        database_provider = database_provider or DEFAULTS["database_provider"]
    else:
        name = typer.prompt("Enter Project Title", default=DEFAULTS["name"])
        description = typer.prompt(
            "Enter Project Description", default=DEFAULTS["description"]
        )
        version = typer.prompt("Enter Project Version", default=DEFAULTS["version"])
        database_type = typer.prompt(
            "Enter Database Type", default=DEFAULTS["database_type"]
        )
        database_provider = typer.prompt(
            "Enter Database Provider", default=DEFAULTS["database_provider"]
        )

    try:
        project_location = path.resolve()

        setup_steps = [
            SetupStructure,
            SetupFiles,
            SetupGithub,
            SetupEnv,
            SetupFileWriter,
            SetupDatabase,
        ]

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
        ) as progress:
            task = progress.add_task("Setting up project", total=len(setup_steps))

            for setup_cls in setup_steps:
                progress.update(task, description=f"Running {setup_cls.__name__}")

                setup_project(
                    project_location,
                    setup_cls,
                    name=name,
                    description=description,
                    version=version,
                    database_type=database_type,
                    database_provider=database_provider,
                )

                progress.advance(task)

        typer.secho(
            "Project setup completed successfully.",
            fg=typer.colors.GREEN,
        )
        typer.secho(
            "Update .env File Content Before Starting The Server",
            fg=typer.colors.MAGENTA,
        )

    except Exception as e:
        typer.secho(
            f"Project setup failed: {e}",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)


@app.command()
def add():
    """Add components to an existing project."""
    console.print("[yellow]Add command not implemented yet[/yellow]")
