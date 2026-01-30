from intuned_cli.utils.help import print_help_and_exit
from intuned_cli.utils.wrapper import cli_command


@cli_command
async def authsession():
    """Manage AuthSessions"""

    print_help_and_exit()
