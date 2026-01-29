import sys

import click
from sifflet_cli import __version__
from sifflet_cli.code.commands import code
from sifflet_cli.configure.commands import configure
from sifflet_cli.ingest.commands import ingest
from sifflet_cli.rules.commands import rules
from sifflet_cli.status.commands import status
from sifflet_sdk.configure.service import ConfigureService
from sifflet_sdk.constants import SIFFLET_CONFIG_CTX
from sifflet_sdk.errors import exception_handler


@exception_handler
def main():
    """Entrypoint"""
    sys.exit(sifflet_cli())  # pylint: disable=E1120


@click.group()
@click.version_option(__version__)
@click.option("--debug", is_flag=True, hidden=True)
@click.pass_context
def sifflet_cli(ctx, debug: bool):
    """Sifflet CLI"""
    sifflet_config = ConfigureService().load_configuration(debug)
    ctx.ensure_object(dict)
    sifflet_config.application_name = f"sifflet-cli-{__version__}"
    ctx.obj[SIFFLET_CONFIG_CTX] = sifflet_config


sifflet_cli.add_command(status)
sifflet_cli.add_command(configure)
sifflet_cli.add_command(rules)
sifflet_cli.add_command(ingest)
sifflet_cli.add_command(code)
