import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import click
import threading
import time
import yaml
from click import Context
from click.types import UUID
from click_option_group import RequiredMutuallyExclusiveOptionGroup, optgroup
from rich.console import Console
from rich.syntax import Syntax
from sifflet_sdk.client.models.as_code_workspace_dto import AsCodeWorkspaceDto
from sifflet_sdk.client.models.workspace_apply_object_response_dto import (
    WorkspaceApplyObjectResponseDto,
)
from sifflet_sdk.client.models.workspace_apply_response_dto import (
    WorkspaceApplyResponseDto,
)
from sifflet_sdk.code.workspace.service import WorkspaceService
from sifflet_sdk.constants import SIFFLET_CONFIG_CTX

WORKSPACE_PLAN_HEADER = "\n--- Workspace plan (dry-run) ---\n"


@click.group()
def workspace():
    """Manage and apply workspaces."""


@workspace.command()
@click.option(
    "--file",
    "-f",
    "file_name",
    required=True,
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="Path of the Workspace YAML file",
)
@click.option(
    "--quiet",
    "quiet",
    is_flag=True,
    help="Print only changes with errors and the summary",
)
@click.pass_context
def plan(ctx: Context, file_name: str, quiet: bool):
    """
    Show the plan for applying the specified workspace (dry-run mode).
    """
    do_plan(WorkspaceService(ctx.obj[SIFFLET_CONFIG_CTX]), file_name, quiet)


@workspace.command()
@click.option(
    "--file",
    "-f",
    "file_name",
    required=True,
    type=click.Path(exists=False),
    help="Path of the Workspace YAML file",
)
@click.option("--name", "-n", "name", required=True, type=str, help="Name of the workspace")
@click.pass_context
def init(ctx: Context, file_name: str, name: str):
    """
    Creates a new Workspace YAML file locally.
    """
    if Path(file_name).exists():
        raise click.BadParameter("File already exists", ctx, param_hint="--file")

    workspace_service = WorkspaceService(ctx.obj[SIFFLET_CONFIG_CTX])
    workspace_service.initialize_workspace(Path(file_name), name)


@workspace.command()
@click.pass_context
def list(ctx: Context):
    """
    List all workspaces.
    """
    workspace_service = WorkspaceService(ctx.obj[SIFFLET_CONFIG_CTX])
    workspace_apply_response: List[AsCodeWorkspaceDto] = workspace_service.list_workspaces()
    # Print list of workspaces
    console = Console()
    for workspace in workspace_apply_response:
        if workspace.description:
            console.print(f" - [bold]{workspace.id}[/bold] - {workspace.name} ({workspace.description})")
        else:
            console.print(f" - [bold]{workspace.id}[/bold] - {workspace.name}")


@workspace.command()
@optgroup.group("Workspace to delete", cls=RequiredMutuallyExclusiveOptionGroup)
@optgroup.option("--id", "id", type=UUID, help="ID of the workspace")
@optgroup.option(
    "--file",
    "-f",
    "file_name",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="Path of the Workspace YAML file",
)
@click.option(
    "--auto-approve",
    is_flag=True,
    help="Skip plan and confirmation, and delete directly.",
)
@click.pass_context
@click.option(
    "--keep-resources",
    "keep_resources",
    is_flag=True,
    help="Keep workspace's resources instead of deleting them",
)
@click.option(
    "--quiet",
    "quiet",
    is_flag=True,
    help="Print only changes with errors and the summary",
)
def delete(
    ctx: Context,
    id: Optional[uuid.UUID],
    file_name: Optional[str],
    auto_approve: bool,
    keep_resources: bool,
    quiet: bool,
):
    """
    Deletes a workspace.
    """
    workspace_service = WorkspaceService(ctx.obj[SIFFLET_CONFIG_CTX])

    if not file_name and not id:
        raise click.BadParameter("Either --file or --id must be provided", ctx, param_hint="--file or --id")

    if auto_approve:
        do_apply_delete(workspace_service, id, file_name, quiet, keep_resources)
        return

    do_plan_delete(workspace_service, id, file_name, quiet, keep_resources)

    confirm = click.prompt("\nDo you really want to delete this workspace? Type 'yes' to confirm", type=str)
    if confirm.strip().lower() != "yes":
        click.echo("Aborted. No changes have been applied.")
        return

    do_apply_delete(workspace_service, id, file_name, quiet, keep_resources)


@workspace.command()
@click.option(
    "--file",
    "-f",
    "file_name",
    required=True,
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="Path of the Workspace YAML file",
)
@click.option(
    "--keep-untracked-resources",
    "keep_untracked_resources",
    is_flag=True,
    help="Keep resources that are not tracked by the workspace anymore instead of deleting them",
)
@click.option(
    "--fail-on-error",
    "fail_on_error",
    is_flag=True,
    help="Fail the entire update if any error is detected",
)
@click.option(
    "--auto-approve",
    is_flag=True,
    help="Skip plan and confirmation, and apply directly.",
)
@click.option(
    "--quiet",
    "quiet",
    is_flag=True,
    help="Print only changes with errors and the summary",
)
@click.pass_context
def apply(
    ctx: Context,
    file_name: str,
    keep_untracked_resources: bool,
    fail_on_error: bool,
    auto_approve: bool,
    quiet: bool,
):
    """
    Apply the specified workspace.
    """
    workspace_service = WorkspaceService(ctx.obj[SIFFLET_CONFIG_CTX])

    if auto_approve:
        # Apply directly without plan or confirmation
        do_apply(workspace_service, file_name, keep_untracked_resources, fail_on_error, quiet)
        return

    # Step 1: Show the plan (dry-run)
    do_plan(workspace_service, file_name, quiet)

    # Step 2: Ask for confirmation
    confirm = click.prompt("\nDo you want to apply these changes? Type 'yes' to confirm", type=str)
    if confirm.strip().lower() != "yes":
        click.echo("Aborted. No changes have been applied.")
        return

    # Step 3: Actually apply (dry_run=False)
    do_apply(workspace_service, file_name, keep_untracked_resources, fail_on_error, quiet)


def print_response(response: WorkspaceApplyResponseDto, is_quiet: bool) -> None:
    console = Console()
    changes = response.changes
    changes_with_errors = filter_changes(changes, {"Error", "Fatal"})

    create_success_count = count_changes(changes, "Create", "Success", "Monitor")
    update_success_count = count_changes(changes, "Update", "Success", "Monitor")
    delete_success_count = count_changes(changes, "Delete", "Success", "Monitor")
    no_change_count = count_changes(changes, "None", "Success", "Monitor")
    error_count = len(changes_with_errors)

    response_dict = {}
    response_dict["changes"] = [
        change.to_dict() for change in changes if change not in changes_with_errors and not is_none_change(change)
    ]
    response_dict["errors"] = [change.to_dict() for change in changes_with_errors]

    if is_quiet:
        response_dict.pop("changes")

    syntax = Syntax(yaml.dump(response_dict, sort_keys=False), "yaml")
    console.print(syntax)

    console.print(f"\nChange summary:")
    console.print(f"- {create_success_count} monitors created")
    console.print(f"- {update_success_count} monitors updated")
    console.print(f"- {delete_success_count} monitors deleted")
    console.print(f"- {no_change_count} monitors without change")
    console.print(f"- {error_count} errors occurred")


def count_changes(
    changes: List[WorkspaceApplyObjectResponseDto],
    change_type: str,
    sub_status: str,
    kind: str,
) -> int:
    return sum(
        1
        for change in changes
        if change.change
        and change.change.type == change_type
        and change.sub_status == sub_status
        and change.kind == kind
    )


def filter_changes(
    changes: List[WorkspaceApplyObjectResponseDto], statuses: set
) -> List[WorkspaceApplyObjectResponseDto]:
    return [change for change in changes if change.status in statuses]


def do_plan(workspace_service, file_name, is_quiet):
    click.echo(WORKSPACE_PLAN_HEADER)
    workspace_apply_response, fatal_error_occurred = call_apply_workspace_and_print_messages_while_waiting_for_response(
        workspace_service, Path(file_name), True, False, False
    )
    print_response(workspace_apply_response, is_quiet)

    if fatal_error_occurred:
        sys.exit(1)


def do_apply(workspace_service, file_name, keep_untracked_resources, fail_on_error, is_quiet):
    click.echo("\n--- Applying workspace ---\n")
    force_delete = not keep_untracked_resources
    workspace_apply_response, fatal_error_occurred = call_apply_workspace_and_print_messages_while_waiting_for_response(
        workspace_service, Path(file_name), False, force_delete, fail_on_error
    )
    print_response(workspace_apply_response, is_quiet)
    if fatal_error_occurred:
        sys.exit(1)


@dataclass
class BackendResponseContainer:
    workspace_apply_response: Optional[WorkspaceApplyResponseDto] = None
    fatal_error_occurred: str = ""


def call_apply_workspace_and_print_messages_while_waiting_for_response(
    workspace_service, workspace_file_name, is_dry_run, force_delete: bool, fail_on_error
) -> Tuple[WorkspaceApplyResponseDto, str]:
    backend_response_container = BackendResponseContainer()
    t = threading.Thread(
        target=call_apply_workspace,
        args=(
            backend_response_container,
            workspace_service,
            workspace_file_name,
            is_dry_run,
            force_delete,
            fail_on_error,
        ),
    )
    t.start()
    elapsed = 0.0
    heartbeat_interval = 0.5  # seconds
    console = Console()

    while t.is_alive():
        t.join(timeout=heartbeat_interval)
        elapsed += heartbeat_interval
        if elapsed % 10 == 0:
            console.print(f"⏳ Working... [{int(elapsed)}s elapsed]")

    assert backend_response_container.workspace_apply_response is not None
    return backend_response_container.workspace_apply_response, backend_response_container.fatal_error_occurred


def call_apply_workspace(
    backend_response_container: BackendResponseContainer,
    workspace_service,
    workspace_file_name,
    dry_run,
    force_delete,
    fail_on_error,
) -> None:
    workspace_apply_response, fatal_error_occurred = workspace_service.apply_workspace(
        workspace_file_name, dry_run, force_delete, fail_on_error
    )
    backend_response_container.workspace_apply_response = workspace_apply_response
    backend_response_container.fatal_error_occurred = fatal_error_occurred


def do_plan_delete(workspace_service, id, file_name, quiet, keep_resources):
    response = call_delete_service(workspace_service, id, file_name, True, keep_resources)
    print_response(response, quiet)


def do_apply_delete(workspace_service, id, file_name, quiet, keep_resources):
    response = call_delete_service(workspace_service, id, file_name, False, keep_resources)
    print_response(response, quiet)


def call_delete_service(workspace_service, id, file_name: str, dry_run: bool, keep_resources: bool):
    cascade_delete = not keep_resources
    if id:
        return workspace_service.delete_workspace_by_id(id, dry_run, cascade_delete)
    else:
        return workspace_service.delete_workspace_by_file_name(Path(file_name), dry_run, cascade_delete)


def is_none_change(change: WorkspaceApplyObjectResponseDto) -> bool:
    return change.change and change.change.type == "None" and change.sub_status == "Success"
