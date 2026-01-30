from typing import Any
from typing import Generator
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from _intuned_runtime_internal.helpers.persistent_store import _PersistentStore  # type: ignore
from _intuned_runtime_internal.helpers.persistent_store import PersistentStoreGetResponse
from _intuned_runtime_internal.helpers.persistent_store import PersistentStoreSetRequest  # type: ignore
from _intuned_runtime_internal.helpers.persistent_store import validate_key


class TestValidateKey:
    def test_valid_key(self):
        assert validate_key("valid_key") == "valid_key"
        assert validate_key("a") == "a"
        assert validate_key("key123") == "key123"

    def test_empty_key_raises_error(self):
        with pytest.raises(ValueError, match="Key must be at least 1 character long"):
            validate_key("")

    def test_forbidden_characters_raise_error(self):
        with pytest.raises(ValueError, match='Key cannot contain the following characters: ":" or "#"'):
            validate_key("key:with:colon")

        with pytest.raises(ValueError, match='Key cannot contain the following characters: ":" or "#"'):
            validate_key("key#with#hash")


@pytest.fixture(autouse=True)
def mock_call_backend() -> Generator[MagicMock, Any, None]:
    """Mock dependencies for API controller tests."""
    with patch("_intuned_runtime_internal.helpers.persistent_store.call_backend_function") as mock_call_backend:
        yield mock_call_backend


class TestCache:
    @pytest.fixture
    def cache(self):
        return _PersistentStore()

    @pytest.mark.asyncio
    async def test_get_returns_value_when_found(self, mock_call_backend: MagicMock, cache: _PersistentStore):
        # Setup
        mock_response = MagicMock()
        mock_response.value = {"value": "cached_data"}
        mock_call_backend.return_value = mock_response

        # Execute
        result = await cache.get("test_key")

        # Assert
        assert result == "cached_data"
        mock_call_backend.assert_called_once_with(
            name="kv-store/test_key", method="GET", validation_model=PersistentStoreGetResponse
        )

    @pytest.mark.asyncio
    async def test_get_returns_none_when_no_response(self, mock_call_backend: MagicMock, cache: _PersistentStore):
        mock_call_backend.return_value = None

        result = await cache.get("test_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_returns_none_when_no_value(self, mock_call_backend: MagicMock, cache: _PersistentStore):
        mock_response = MagicMock()
        mock_response.value = None
        mock_call_backend.return_value = mock_response

        result = await cache.get("test_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_validates_key(self, mock_call_backend: MagicMock, cache: _PersistentStore):
        with pytest.raises(ValueError):
            await cache.get("invalid:key")

    @pytest.mark.asyncio
    async def test_set_calls_backend_correctly(self, mock_call_backend: MagicMock, cache: _PersistentStore):
        test_value = {"data": "test"}

        await cache.set("test_key", test_value)

        mock_call_backend.assert_called_once()
        call_args = mock_call_backend.call_args

        assert call_args[0][0] == "kv-store/test_key"  # first positional arg
        assert call_args[1]["method"] == "PUT"
        assert call_args[1]["validation_model"].__name__ == "PersistentStoreSetResponse"
        assert isinstance(call_args[1]["params"], PersistentStoreSetRequest)
        assert call_args[1]["params"].value == test_value

    @pytest.mark.asyncio
    async def test_set_validates_key(self, mock_call_backend: MagicMock, cache: _PersistentStore):
        with pytest.raises(ValueError):
            await cache.set("invalid#key", "value")
