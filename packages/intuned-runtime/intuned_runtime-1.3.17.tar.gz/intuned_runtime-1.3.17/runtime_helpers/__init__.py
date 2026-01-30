from logging import getLogger

from _intuned_runtime_internal.helpers import extend_payload
from _intuned_runtime_internal.helpers import extend_timeout
from _intuned_runtime_internal.helpers.attempt_store import attempt_store
from _intuned_runtime_internal.helpers.get_auth_session_parameters import get_auth_session_parameters
from _intuned_runtime_internal.helpers.persistent_store import persistent_store

logger = getLogger(__name__)

logger.warning(
    "The 'runtime_helpers' module is deprecated and will be removed in future versions. Please use 'intuned_runtime' instead."
)

__all__ = ["extend_payload", "extend_timeout", "get_auth_session_parameters", "attempt_store", "persistent_store"]
