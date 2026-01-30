from intuned_cli.controller.provision import provision_project
from intuned_cli.controller.provision import validate_intuned_project
from intuned_cli.controller.provision import validate_project_name
from intuned_cli.utils.api_helpers import get_intuned_settings_file_name
from intuned_cli.utils.backend import get_intuned_api_auth_credentials
from intuned_cli.utils.error import CLIError
from intuned_cli.utils.prompts import prompt_for_project_name
from intuned_cli.utils.wrapper import cli_command


@cli_command
async def provision(
    project_name: str | None = None,
    /,
    *,
    workspace_id: str | None = None,
    api_key: str | None = None,
):
    """Provisions project to Intuned platform.

    Args:
        project_name (str | None, optional): Project name.
        workspace_id (str | None, optional): Intuned Workspace ID.
        api_key (str | None, optional): Intuned API Key.
    """
    return await _provision_impl(
        project_name,
        workspace_id,
        api_key,
    )


@cli_command
async def save(
    project_name: str | None = None,
    /,
    *,
    workspace_id: str | None = None,
    api_key: str | None = None,
) -> None:
    """Provisions project to Intuned platform. (Deprecated, use 'provision' instead)

    Args:
        project_name (str | None, optional): Project name.
        workspace_id (str | None, optional): Intuned Workspace ID.
        api_key (str | None, optional): Intuned API Key.
    """

    return await _provision_impl(
        project_name,
        workspace_id,
        api_key,
    )


async def _provision_impl(
    project_name: str | None,
    workspace_id: str | None,
    api_key: str | None,
) -> None:
    try:
        intuned_json = await validate_intuned_project()
    except CLIError as e:
        raise CLIError(
            f"[bold red]Project to be provisioned is not valid:[/bold red][bright_red] {e}[/bright_red]\n",
            auto_color=False,
        ) from e

    project_name = project_name or intuned_json.project_name

    if not project_name:
        project_name = await prompt_for_project_name(validate=validate_project_name)

    if not project_name:
        raise CLIError(
            f"Project name is required. Set it in {await get_intuned_settings_file_name()} or provide it as an argument by running 'intuned provision <project-name>'."
        )

    validate_project_name(project_name)

    workspace_id, api_key = await get_intuned_api_auth_credentials(
        intuned_json=intuned_json, workspace_id=workspace_id, api_key=api_key
    )

    await provision_project(
        project_name=project_name,
        workspace_id=workspace_id,
        api_key=api_key,
    )
