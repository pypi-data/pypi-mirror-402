import click
from sifflet_cli.logger import logger
from sifflet_sdk.constants import SIFFLET_CONFIG_CTX
from sifflet_sdk.ingest.service import IngestionService


@click.group()
def ingest():
    """Control ingestion of tools into Sifflet."""


@ingest.command()
@click.option(
    "--project-name",
    "-p",
    "project_name",
    required=True,
    type=str,
    help="The name of your dbt project (in your dbt_project.yml file)",
)
@click.option(
    "--target",
    "-t",
    type=str,
    required=True,
    help="The target value of the profile (in your dbt_project.yml file)",
)
@click.option(
    "--input-folder",
    "-i",
    "input_folder",
    required=True,
    type=str,
    help="The dbt execution folder",
)
@click.pass_context
def dbt(ctx, project_name: str, target: str, input_folder: str):
    """
    Ingest dbt metadata files into Sifflet
    """
    sifflet_config = ctx.obj[SIFFLET_CONFIG_CTX]

    ingestion_service = IngestionService(sifflet_config)
    dbt_sent = ingestion_service.ingest_dbt(project_name, target, input_folder)
    if dbt_sent:
        logger.info("DBT metadata sent with SUCCESS.")
