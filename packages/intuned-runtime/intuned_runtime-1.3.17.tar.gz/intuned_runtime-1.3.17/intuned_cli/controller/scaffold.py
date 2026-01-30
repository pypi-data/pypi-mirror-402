from json import JSONDecodeError

import httpx
from anyio import Path
from pydantic import BaseModel
from pydantic import Field
from pydantic import ValidationError

from intuned_cli.types import DirectoryNode
from intuned_cli.types import FileSystemTree
from intuned_cli.utils.api_helpers import assert_api_file_exists
from intuned_cli.utils.auth_session_helpers import assert_auth_enabled
from intuned_cli.utils.backend import get_base_url
from intuned_cli.utils.console import console
from intuned_cli.utils.error import CLIError


class AuthSessionTemplateResponse(BaseModel):
    model_config = {"populate_by_name": True}
    auth_sessions: FileSystemTree = Field(alias="auth-sessions")


async def scaffold_auth_session_files():
    await assert_auth_enabled()

    create_exists, check_exists = True, True
    try:
        await assert_api_file_exists("auth-sessions", "create")
    except CLIError:
        create_exists = False
    try:
        await assert_api_file_exists("auth-sessions", "check")
    except CLIError:
        check_exists = False

    if create_exists and check_exists:
        console.print("[bold green]AuthSession files already eixst[/bold green]")
        return

    console.print("[bold green]Scaffolding...[/bold green]")

    base_url = get_base_url()
    url = f"{base_url}/api/v1/templates/authsession?language=python"
    headers = {
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise CLIError(f"""Failed to fetch AuthSession template
Got {response.status_code} {response.text}""")

    try:
        template = AuthSessionTemplateResponse.model_validate(response.json())
    except JSONDecodeError as e:
        raise CLIError(f"Failed to parse AuthSession template response: {e}") from e
    except ValidationError as e:
        raise CLIError(f"Invalid AuthSession template response: {e}") from e

    cwd = Path()
    for file_name in template.auth_sessions.root:
        node = template.auth_sessions.root[file_name]
        if isinstance(node, DirectoryNode):
            continue
        file_path = cwd / "auth-sessions" / file_name
        await file_path.parent.mkdir(parents=True, exist_ok=True)
        if await file_path.exists():
            continue
        await file_path.write_text(node.file.contents)
        console.print(f"[bold green]Written [underline]{file_path}[/underline][/bold green]")
