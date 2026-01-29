import click

from pathlib import Path
from typing import List
from docgen.generator import check_module, get_python_files, process_module


@click.command()
@click.argument(
    "paths", nargs=-1, type=click.Path(exists=True, path_type=Path)
)
@click.option(
    "--check", is_flag=True, help="Only check for missing docstrings."
)
@click.option(
    "--recursive", is_flag=True, help="Recursively process directories."
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output.")
@click.option(
    "--full",
    is_flag=True,
    help="Generate more complete docstring with additional parameters.",
)
def main(
    paths: List[str], check: bool, recursive: bool, verbose: bool, full: bool
):
    """Generate NumPy-style docstrings for Python files."""
    if not paths:
        paths = [str(Path.cwd())]

    root_dir = Path.cwd()
    python_files = get_python_files(paths, recursive=recursive, root=root_dir)

    if not python_files:
        click.echo("No Python files found.")
        return

    for file in python_files:
        if verbose:
            click.echo(f"{'Checking' if check else 'Processing'} {file}")

        if check:
            click.echo(f"[CHECK] {file.name}")
            check_module(file_path=file)
        else:
            click.echo(f"[GENERATE] Generating docstring in {file.name}")
            process_module(file_path=file, docstring_type=full)
