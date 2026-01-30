import time
from pathlib import Path

import typer
from rich.align import Align
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
)
from rich.prompt import Prompt
from rich.text import Text

from builders_hut.setups import (
    SetupDatabase,
    SetupEnv,
    SetupFiles,
    SetupFileWriter,
    SetupGithub,
    SetupStructure,
)
from builders_hut.utils import setup_project

# ------------------------------------------------------------------
# App setup
# ------------------------------------------------------------------

console = Console()
app = typer.Typer(
    invoke_without_command=True,
    no_args_is_help=True,
)

APP_VERSION = "0.4.3"

BANNER = r"""
 ____        _ _     _                 _   _       _   
| __ ) _   _(_) | __| | ___ _ __ ___  | | | |_   _| |_ 
|  _ \| | | | | |/ _` |/ _ \ '__/ __| | |_| | | | | __|
| |_) | |_| | | | (_| |  __/ |  \__ \ |  _  | |_| | |_ 
|____/ \__,_|_|_|\__,_|\___|_|  |___/ |_| |_|\__,_|\__|
"""

# ------------------------------------------------------------------
# UI helpers
# ------------------------------------------------------------------


def render_header() -> Panel:
    text = Text()
    text.append(BANNER, style="bold cyan")
    text.append(f"\nVersion {APP_VERSION}\n", style="bold cyan")

    return Panel(
        Align.center(text),
        border_style="cyan",
        padding=(1, 2),
    )


def clear_and_render(panel: Panel):
    console.clear()
    console.print(render_header())
    console.print(panel)


def ask_question(title: str, question: str, default: str) -> str:
    body = Text()
    body.append(f"{title}\n\n", style="bold cyan")
    body.append(question, style="white")

    panel = Panel(
        body,
        border_style="cyan",
        padding=(1, 2),
    )

    clear_and_render(panel)
    return Prompt.ask("", default=default)


# ------------------------------------------------------------------
# Wizard
# ------------------------------------------------------------------


def run_wizard():
    answers = {}

    answers["name"] = ask_question(
        "Project Name",
        "Enter your project name",
        Path.cwd().name,
    )

    answers["description"] = ask_question(
        "Project Description",
        "Describe your project",
        "A new project",
    )

    answers["version"] = ask_question(
        "Project Version",
        "Initial project version",
        "0.1.0",
    )

    answers["database_type"] = ask_question(
        "Database Type",
        "Choose database type (sql / nosql)",
        "sql",
    )

    answers["database_provider"] = ask_question(
        "Database Provider",
        "postgres / mysql / sqlite / mongodb",
        "postgres",
    )

    return answers


# ------------------------------------------------------------------
# Progress runner (INSIDE BOX)
# ------------------------------------------------------------------


"""Steps"""

STEPS = {
    "SetupStructure": "Setting up project structure",
    "SetupFiles": "Adding base files",
    "SetupGithub": "Setting up GitHub repository",
    "SetupEnv": "Installing packages and creating .env",
    "SetupFileWriter": "Updating file contents",
    "SetupDatabase": "Setting up database files",
}


def run_setup_with_progress(
    project_location: Path,
    setup_steps: list,
    **kwargs,
):
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(),
    )

    task = progress.add_task("Initializing project...", total=len(setup_steps))

    panel = Panel(
        progress,
        title="Setting up project",
        border_style="cyan",
        padding=(1, 2),
    )

    with Live(panel, console=console, refresh_per_second=10):
        for step in setup_steps:
            progress.update(task, description=f"{STEPS[step.__name__]}")
            setup_project(project_location, step, **kwargs)
            time.sleep(0.5)
            progress.advance(task)


# ------------------------------------------------------------------
# Final screen
# ------------------------------------------------------------------


def show_success():
    text = Text()
    text.append("✅ Project setup completed successfully!\n\n", style="bold green")
    text.append("NEXT STEPS\n", style="bold cyan")
    text.append(
        "\n1. Update environment variables\n"
        "   • Open .env and fill required values\n\n"
        "2. Run database migrations\n"
        '   • alembic revision --autogenerate -m "initial migration"\n'
        "   • alembic upgrade head\n\n"
        "3. Start the server\n"
        "   • python run.py\n",
        style="white",
    )

    text.append(
        "\nNote:- Sample model with respective repository and service is created along with the project for user reference.\n"
        "It is suggested to go throw them once before removing anything\n",
        style="yellow",
    )

    panel = Panel(
        Align.left(text),
        border_style="green",
        padding=(1, 2),
        title="🚀 Ready",
    )

    clear_and_render(panel)


# ------------------------------------------------------------------
# Typer callbacks & commands
# ------------------------------------------------------------------


@app.callback()
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit",
        is_eager=True,
    ),
):
    if version:
        console.print(f"[bold green]hut version {APP_VERSION}[/bold green]")
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command()
def build(
    path: Path = typer.Option(
        Path.cwd(),
        "--path",
        "-p",
        help="Project directory",
    ),
    accept_default: bool = typer.Option(
        False,
        "--accept-defaults",
        "-y",
        help="Run with default values",
    ),
):
    """
    Build a new project using an interactive wizard.
    """

    DEFAULTS = {
        "name": Path.cwd().name,
        "description": "A new project",
        "version": "0.1.0",
        "database_type": "sql",
        "database_provider": "postgres",
    }

    try:
        if accept_default:
            answers = DEFAULTS
        else:
            answers = run_wizard()

        setup_steps = [
            SetupStructure,
            SetupFiles,
            SetupGithub,
            SetupEnv,
            SetupFileWriter,
            SetupDatabase,
        ]

        run_setup_with_progress(
            project_location=path.resolve(),
            setup_steps=setup_steps,
            **answers,
        )

        show_success()

    except Exception as e:
        error_panel = Panel(
            Text(f"❌ Project setup failed\n\n{e}", style="red"),
            border_style="red",
            padding=(1, 2),
        )
        clear_and_render(error_panel)
        raise typer.Exit(code=1)


@app.command()
def add():
    panel = Panel(
        Text("Add command not implemented yet", style="yellow"),
        border_style="yellow",
        padding=(1, 2),
    )
    clear_and_render(panel)
