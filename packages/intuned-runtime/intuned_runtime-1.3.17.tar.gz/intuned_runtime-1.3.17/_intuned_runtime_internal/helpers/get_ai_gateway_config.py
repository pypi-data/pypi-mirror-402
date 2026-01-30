from _intuned_runtime_internal.backend_functions._call_backend_function import build_backend_functions_path
from _intuned_runtime_internal.backend_functions._call_backend_function import get_backend_functions_info
from _intuned_runtime_internal.context.context import IntunedContext
from _intuned_runtime_internal.env import get_api_key


def get_ai_gateway_config():
    """
    Retrieves the base URL and API key for the Intuned AI Gateway.

    Returns:
        tuple[str, str]: A tuple containing (base_url, api_key)
    """
    functions_domain, workspace_id, project_id = get_backend_functions_info()
    base_url = build_backend_functions_path("intuned-ai-gateway", functions_domain, workspace_id, project_id)
    api_key = IntunedContext.current().functions_token or get_api_key() or ""
    return base_url, api_key
