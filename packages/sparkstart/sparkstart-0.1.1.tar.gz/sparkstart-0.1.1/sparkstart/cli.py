import pathlib
import typer
import shutil
from sparkstart.core import create_project, delete_project


app = typer.Typer(
    help="sparkstart – create a new project repository quickly",
    invoke_without_command=True,  # allows root alias
    no_args_is_help=True,
)


# --- root alias ----------------------------------------------------
@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    # name argument removed to avoid "stealing" the subcommand
):
    """
    sparkstart – Start your new project in seconds.
    
    Usage:
        sparkstart new <name>
        sparkstart delete <name>
    """
    if ctx.invoked_subcommand is None:
        # If no subcommand is provided, show the help message
        print(ctx.get_help())
        raise typer.Exit()


# --- explicit sub‑command -----------------------------------------
@app.command()
def new(
    name: str,
    github: bool = typer.Option(False, "--github", help="Push to GitHub"),
    lang: str = typer.Option("python", "--lang", "-l", help="Language: python, rust, javascript, cpp"),
):
    """Create a new project folder NAME (optionally push to GitHub)."""
    create_project(pathlib.Path.cwd() / name, github, lang)



@app.command()
def delete(
    name: str,
    github: bool = typer.Option(False, "--github"),
    force: bool = typer.Option(False, "--yes", "-y"),
):
    target = pathlib.Path.cwd() / name
    if not force:
        typer.confirm(f"Delete {'and remote ' if github else ''}{target} ?", abort=True)

    try:
        from sparkstart.core import delete_project

        delete_project(target, github)
        typer.secho("Project deleted !", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"Failed : {e}", fg=typer.colors.RED)
