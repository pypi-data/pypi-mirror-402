import io
import json
import re
from typing import Any

import pathspec
from anyio import Path
from dotenv.main import DotEnv
from pydantic import BaseModel
from pydantic import Field
from pydantic import ValidationError

from _intuned_runtime_internal.env import api_key_env_var_key
from _intuned_runtime_internal.env import project_env_var_key
from _intuned_runtime_internal.env import workspace_env_var_key
from intuned_cli.types import DirectoryNode
from intuned_cli.types import FileNode
from intuned_cli.types import FileNodeContent
from intuned_cli.types import FileSystemTree
from intuned_cli.utils.api_helpers import get_intuned_settings_file
from intuned_cli.utils.api_helpers import load_intuned_json
from intuned_cli.utils.backend import get_http_client
from intuned_cli.utils.console import console
from intuned_cli.utils.error import CLIError
from intuned_cli.utils.exclusions import exclusions


class IntunedPyprojectToml(BaseModel):
    class _Tool(BaseModel):
        class _Poetry(BaseModel):
            dependencies: dict[str, Any]

        poetry: _Poetry

    tool: _Tool


async def validate_intuned_project():
    cwd = await Path().resolve()

    pyproject_toml_path = cwd / "pyproject.toml"

    if not await pyproject_toml_path.exists():
        raise CLIError("pyproject.toml file is missing in the current directory.")

    intuned_json = await load_intuned_json()

    api_folder = cwd / "api"
    if not await api_folder.exists() or not await api_folder.is_dir():
        raise CLIError("api directory does not exist in the current directory.")

    if intuned_json.auth_sessions.enabled:
        auth_sessions_folder = cwd / "auth-sessions"
        if not await auth_sessions_folder.exists() or not await auth_sessions_folder.is_dir():
            raise CLIError(
                """AuthSessions are enabled and auth-sessions directory does not exist in the current directory.
Use 'intuned authsession scaffold' to scaffold the auth-sessions directory."""
            )

    return intuned_json


def validate_project_name(project_name: str):
    if len(project_name) > 200:
        raise CLIError("Project name must be 200 characters or less.")

    project_name_regex = r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$"
    if not re.match(project_name_regex, project_name):
        raise CLIError("Project name can only contain lowercase letters, numbers, hyphens, and underscores in between.")

    try:
        import uuid

        uuid.UUID(project_name)
        raise CLIError("Project name cannot be a UUID.")
    except ValueError:
        # Not a valid UUID, continue
        pass


async def get_file_tree_from_project(path: Path, *, exclude: list[str] | None = None):
    # Create pathspec object for gitignore-style pattern matching
    exclude = exclude or []
    gitignore_file = await find_gitignore_file(path)
    if gitignore_file:
        content = await gitignore_file.read_text()
        exclude.extend(content.splitlines())
    spec = pathspec.PathSpec.from_lines(pathspec.patterns.gitwildmatch.GitWildMatchPattern, exclude)

    async def traverse(current_path: Path) -> tuple[FileSystemTree, list[str]]:
        tree = FileSystemTree(root={})
        filenames: list[str] = []
        async for entry in current_path.iterdir():
            relative_path_name = entry.relative_to(path).as_posix()
            basename = entry.name

            # Check if this path should be excluded
            if spec and spec.match_file(relative_path_name):
                continue

            if await entry.is_dir():
                subtree, subfiles = await traverse(entry)
                tree.root[basename] = DirectoryNode(directory=subtree)
                filenames.extend(subfiles)
            elif await entry.is_file():
                tree.root[basename] = FileNode(file=FileNodeContent(contents=await entry.read_text()))
                filenames.append(relative_path_name)
        return tree, filenames

    tree, filenames = await traverse(path)
    console.print("[cyan]Files to be provisioned:[/cyan]")
    console.print(f" {'\n '.join(filenames)}")
    return tree


async def map_file_tree_to_ide_file_tree(file_tree: FileSystemTree):
    if file_tree.root.get("Intuned.json") is None:
        settings_file = await get_intuned_settings_file()
        text_content = await Path(settings_file.file_path).read_text()
        parsed_content = settings_file.parse(text_content)
        json_content = json.dumps(parsed_content, indent=2)
        file_tree.root["Intuned.json"] = FileNode(file=FileNodeContent(contents=json_content))


class UpsertProjectResponse(BaseModel):
    model_config = {"populate_by_name": True}

    id: str
    enable_first_run_experience: bool | None = Field(alias="enableFirstRunExperience", default=None)
    environment_variables_keys: list[str] = Field(alias="environmentVariablesKeys", default_factory=list)


async def provision_project(
    *,
    project_name: str,
    workspace_id: str,
    api_key: str,
    silent: bool = False,
):
    cwd = await Path().resolve()
    file_tree = await get_file_tree_from_project(cwd, exclude=exclusions)
    await map_file_tree_to_ide_file_tree(file_tree)

    payload: dict[str, Any] = {
        "codeTree": file_tree.model_dump(mode="json"),
        "platformType": "CLI",
        "language": "python",
    }

    async with get_http_client(
        workspace_id=workspace_id,
        project_name=project_name,
        api_key=api_key,
    ) as client:
        response = await client.put("", json=payload)
        if response.status_code < 200 or response.status_code >= 300:
            if response.status_code == 401:
                raise CLIError(
                    "Invalid API key. The provided API key is not authorized to access this workspace.\n"
                    "Please verify your API key at: https://app.intuned.io/settings/api-keys"
                )

            raise CLIError(
                f"[red bold]Project provisioning failed:[/red bold]\n"
                f"[bright_red]Server returned status {response.status_code}[/bright_red]\n"
                f"[bright_red]Response: {response.text}[/bright_red]\n\n"
                f"[yellow]Common causes:[/yellow]\n"
                f"  • Invalid workspace ID or project name\n"
                f"  • Insufficient permissions\n"
                f"  • Network connectivity issues\n"
                f"  • Project structure validation errors"
            )

    if not silent:
        console.print("[green]Project provisioned successfully.[/green]")
    try:
        response = UpsertProjectResponse.model_validate(response.json())
    except ValidationError:
        console.print(f"[yellow]Could not parse response:[/yellow]\n {response.text}")
        return None, None

    dotenv_path = cwd / ".env"
    if not await dotenv_path.exists():
        content_to_write = f"""{workspace_env_var_key}={workspace_id}
{project_env_var_key}={response.id}
{api_key_env_var_key}={api_key}
"""
        await dotenv_path.write_text(content_to_write)
        console.print("[green]Created .env with project credentials.[/green]")
        return response, dict[str, str | None]()

    dotenv_content = await dotenv_path.read_text()
    dotenv = DotEnv(
        dotenv_path=None,
        stream=io.StringIO(dotenv_content),
    ).dict()
    content_to_append = ""
    project_credentials_env_vars = {
        workspace_env_var_key: workspace_id,
        project_env_var_key: response.id,
        api_key_env_var_key: api_key,
    }

    for env_var, value in project_credentials_env_vars.items():
        if dotenv.get(env_var) == value:
            continue
        if dotenv.get(env_var) is not None:
            console.print(
                f"[yellow]Warning: Existing {env_var} in .env has invalid value. Appending correct value.[/yellow]"
            )
        content_to_append += f"\n{env_var}={value}"

    if len(content_to_append.strip()) > 0:
        await dotenv_path.write_text(f"{dotenv_content}\n{content_to_append}\n")
        console.print("[green]Updated .env with project credentials.[/green]")

    dotenv_to_return = dotenv.copy()
    for key in [
        project_env_var_key,
        workspace_env_var_key,
        api_key_env_var_key,
    ]:
        if key in dotenv_to_return:
            del dotenv_to_return[key]

    return response, dotenv_to_return


async def find_gitignore_file(project_path: Path) -> Path | None:
    current_directory = project_path

    while True:
        gitignore_path = current_directory / ".gitignore"
        if await gitignore_path.exists():
            return gitignore_path
        parent_directory = current_directory.parent
        if parent_directory == current_directory:
            break
        current_directory = parent_directory
    return None
