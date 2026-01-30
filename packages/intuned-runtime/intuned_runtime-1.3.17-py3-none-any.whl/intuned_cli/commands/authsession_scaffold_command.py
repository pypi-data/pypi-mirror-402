from intuned_cli.controller.scaffold import scaffold_auth_session_files
from intuned_cli.utils.wrapper import cli_command


@cli_command
async def authsession__scaffold():
    """Scaffold AuthSession API files"""

    await scaffold_auth_session_files()
