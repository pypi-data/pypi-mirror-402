import asyncio
import logging
import os
import sys

import arguably
from dotenv import find_dotenv
from dotenv import load_dotenv

import intuned_cli.commands  # pyright: ignore[reportUnusedImport] # noqa: F401
from _intuned_runtime_internal.context.context import IntunedContext
from intuned_cli.utils.api_helpers import load_intuned_json
from intuned_cli.utils.error import CLIExit

logging.basicConfig(level=logging.WARNING, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logging.getLogger().setLevel(logging.WARNING)
logging.getLogger("runtime").setLevel(logging.INFO)
logging.getLogger("intuned_runtime").setLevel(logging.INFO)
logging.getLogger("intuned_browser").setLevel(logging.INFO)
logging.getLogger("api").setLevel(logging.INFO)
logging.getLogger("auth-sessions").setLevel(logging.INFO)
logging.getLogger("hooks").setLevel(logging.INFO)


def run():
    dotenv = find_dotenv(usecwd=True)
    if dotenv:
        load_dotenv(dotenv, override=True)
    from _intuned_runtime_internal.env import cli_env_var_key
    from _intuned_runtime_internal.env import workspace_env_var_key

    os.environ[cli_env_var_key] = "true"
    os.environ["RUN_ENVIRONMENT"] = "AUTHORING"

    if not os.environ.get("FUNCTIONS_DOMAIN"):
        from intuned_cli.utils.backend import get_base_url

        os.environ["FUNCTIONS_DOMAIN"] = get_base_url().replace("/$", "")
    try:
        intuned_json = asyncio.run(load_intuned_json())
        if intuned_json.workspace_id:
            os.environ[workspace_env_var_key] = intuned_json.workspace_id
    except Exception:
        pass
    try:
        with IntunedContext():
            arguably.run(name="intuned", output=sys.stderr)
            return 0
    except CLIExit as e:
        return e.code


__all__ = ["run"]
