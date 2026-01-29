from .run_api_errors import RunApiError


class AuthSessionsNotEnabledError(RunApiError):
    def __init__(self):
        super().__init__(
            "AuthSessions are not enabled",
            "AuthRequiredError",
        )
