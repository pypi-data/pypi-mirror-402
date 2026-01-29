import click
from rich import print as rich_print
from sifflet_cli import __version__
from sifflet_sdk.constants import SIFFLET_CONFIG_CTX
from sifflet_sdk.status.service import StatusService


@click.command()
@click.pass_context
def status(ctx):
    """
    Display basic status of sifflet cli
    """
    sifflet_config = ctx.obj[SIFFLET_CONFIG_CTX]

    show_status: str = f"""
Sifflet version = {__version__}
Tenant = {sifflet_config.backend_url or sifflet_config.tenant}"""

    rich_print(show_status)

    status_service = StatusService(sifflet_config)
    result: bool = status_service.check_status()
    if result:
        rich_print("[bold green]Status = OK[/bold green]")
    else:
        rich_print("[bold red]Status = KO[/bold red]")
