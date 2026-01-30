from collections.abc import Callable
from typing import Any
from uuid import UUID

import questionary

from intuned_cli.utils.console import console
from intuned_cli.utils.console import questionary_output
from intuned_cli.utils.error import CLIAbortError
from intuned_cli.utils.error import CLIError


async def prompt_for_project_name(validate: Callable[[str], Any]) -> str:
    def _validate(value: str) -> bool | str:
        value = value.strip()
        try:
            validate(value)
            return True
        except CLIError as e:
            return str(e)

    project_name = await questionary.text(
        "Project name (required to save/deploy):",
        validate=_validate,
        output=questionary_output,
    ).ask_async(kbi_msg="")
    if project_name is None:
        raise CLIAbortError()
    return project_name.strip()


async def prompt_for_workspace_id() -> str:
    workspace_id = await questionary.text(
        "Workspace ID (required to save/deploy):",
        validate=_validate_uuid,
        output=questionary_output,
    ).ask_async(kbi_msg="")
    if workspace_id is None:
        raise CLIAbortError()
    return workspace_id.strip()


async def prompt_for_api_key() -> str:
    console.print("Get your API key at: https://app.intuned.io/settings/api-keys")
    api_key = await questionary.password(
        "API key (required to save/deploy):",
        validate=_validate_api_key,
        output=questionary_output,
    ).ask_async(kbi_msg="")
    if api_key is None:
        raise CLIAbortError()
    return api_key.strip()


def _validate_uuid(value: str):
    value = value.strip()
    try:
        UUID(value)
        return True
    except Exception:
        return "Workspace ID must be a valid UUID"


def _validate_api_key(value: str):
    value = value.strip()
    issues: list[str] = []
    if len(value) != 36:
        issues.append("API key must be 36 characters long")
    if not value.startswith("in1_"):
        issues.append("API Key must start with 'in1_'")
    if " " in value:
        issues.append("API Key cannot contain spaces")

    return ", ".join(issues) if issues else True
