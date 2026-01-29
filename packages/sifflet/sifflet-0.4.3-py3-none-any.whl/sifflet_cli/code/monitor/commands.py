from pathlib import Path

import click
from click import Context
from sifflet_sdk.code.workspace.service import WorkspaceService
from sifflet_sdk.constants import SIFFLET_CONFIG_CTX


@click.group()
def monitor():
    """Manage monitors."""


@monitor.command()
@click.option(
    "--file",
    "-f",
    "file_name",
    required=True,
    type=click.Path(),
    help="Path of the Monitor YAML file",
)
@click.option("--name", "-n", "name", required=True, type=str, help="Name of the monitor")
@click.pass_context
def init(ctx: Context, file_name: str, name: str):
    """
    Creates a new Monitor YAML file locally.
    """
    if Path(file_name).exists():
        raise click.BadParameter("File already exists", ctx, param_hint="--file")

    sifflet_config = ctx.obj[SIFFLET_CONFIG_CTX]
    workspace_service = WorkspaceService(sifflet_config)
    workspace_service.initialize_monitor(Path(file_name), name)
