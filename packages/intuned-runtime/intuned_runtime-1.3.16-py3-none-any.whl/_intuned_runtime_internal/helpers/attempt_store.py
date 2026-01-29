from typing import Any

from _intuned_runtime_internal.context.context import IntunedContext


class _AttemptStore:
    def get(self, key: str, default: Any = None) -> Any:
        return IntunedContext.current().store.get(key, default)

    def set(self, key: str, value: Any) -> None:
        IntunedContext.current().store[key] = value


attempt_store = _AttemptStore()
