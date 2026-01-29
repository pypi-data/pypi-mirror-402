"""CLI commands for genome."""

import json
from pathlib import Path

import click


@click.group()
@click.version_option()
def cli() -> None:
    """Genome CLI - Analyze dbt manifest.json files."""
    pass


@cli.command()
@click.argument(
    "manifest_path",
    type=click.Path(exists=True, path_type=Path),
    default="target/manifest.json",
)
def sequence(manifest_path: Path) -> None:
    """Count the number of nodes in a dbt manifest.json file.

    MANIFEST_PATH: Path to the manifest.json file (default: target/manifest.json)
    """
    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Invalid JSON in manifest file: {e}")
    except Exception as e:
        raise click.ClickException(f"Error reading manifest file: {e}")

    nodes = manifest.get("nodes", {})
    node_count = len(nodes)

    click.echo(f"Total nodes: {node_count}")


if __name__ == "__main__":
    cli()
