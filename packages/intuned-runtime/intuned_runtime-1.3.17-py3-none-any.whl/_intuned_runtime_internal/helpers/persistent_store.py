import re
from typing import Any

from pydantic import BaseModel

from _intuned_runtime_internal.backend_functions._call_backend_function import call_backend_function

forbidden_characters = re.compile(r"[:#]")


class PersistentStoreGetResponse(BaseModel):
    value: dict[str, Any] | None = None


class PersistentStoreSetResponse(BaseModel):
    pass


class PersistentStoreSetRequest(BaseModel):
    value: Any


def validate_key(key: str) -> str:
    if len(key) < 1:
        raise ValueError("Key must be at least 1 character long")

    if forbidden_characters.search(key):
        raise ValueError('Key cannot contain the following characters: ":" or "#"')

    return key


class _PersistentStore:
    """
    A persistent key-value store for storing and retrieving data.

    The _PersistentStore provides a simple interface to store and retrieve values
    by key. Keys must be at least 1 character long and cannot contain ":" or "#".

    Attributes:
        None
    """

    async def get(self, key: str) -> Any:
        """
        Retrieves a value from the store by key.

        Args:
            key: The key to retrieve the value for. Must be at least 1 character
                long and cannot contain ":" or "#".

        Returns:
            The value associated with the key, or None if not found.

        Raises:
            ValueError: If the key is invalid (less than 1 character or contains
                forbidden characters).

        Example:
            ```python
            value = await store.get('my_key')
            ```
        """
        parsed_key = validate_key(key)
        response = await call_backend_function(
            name=f"kv-store/{parsed_key}",
            method="GET",
            validation_model=PersistentStoreGetResponse,
        )
        if not response or not response.value:
            return None
        return response.value["value"]

    async def set(self, key: str, value: Any) -> None:
        """
        Sets a value in the store by key.

        Args:
            key: The key to set the value for. Must be at least 1 character
                long and cannot contain ":" or "#".
            value: The value to store. Can be any JSON-serializable type.

        Returns:
            None

        Raises:
            ValueError: If the key is invalid (less than 1 character or contains
                forbidden characters).

        Example:
            ```python
            await store.set('my_key', {'foo': 'bar'})
            ```
        """
        key_result = validate_key(key)
        request_params = PersistentStoreSetRequest(value=value)

        await call_backend_function(
            f"kv-store/{key_result}", validation_model=PersistentStoreSetResponse, method="PUT", params=request_params
        )


persistent_store = _PersistentStore()
