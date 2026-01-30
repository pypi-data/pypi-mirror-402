"""Unit types for the downmixer.providers.connections module."""

from unittest.mock import MagicMock

import pytest

from downmixer.providers.connections import (
    AuthenticatedConnection,
    Connection,
)
from downmixer.types.exceptions import NotAuthenticatedException, NotConnectedException
from downmixer.types.library import ResourceType


class ConcreteConnection(Connection):
    """Concrete implementation of Connection for testing."""

    _default_options = {"default_key": "default_value"}

    def initialize(self) -> bool:
        self._initialized = True
        return True

    def check_valid_url(self, url: str, type_filter: list[ResourceType] = None) -> bool:
        return url.startswith("test://")

    def get_resource_type(self, value: str) -> ResourceType | None:
        if "song" in value:
            return ResourceType.SONG
        return None


class ConcreteAuthenticatedConnection(AuthenticatedConnection):
    """Concrete implementation of AuthenticatedConnection for testing."""

    _default_options = {"auth_key": "auth_value"}

    def initialize(self) -> bool:
        self._initialized = True
        return True

    def authenticate(self, **kwargs) -> bool:
        self._authenticated = True
        return True

    def check_valid_url(self, url: str, type_filter: list[ResourceType] = None) -> bool:
        return url.startswith("auth://")

    def get_resource_type(self, value: str) -> ResourceType | None:
        return ResourceType.SONG


class TestNotConnectedException:
    """Tests for NotConnectedException."""

    def test_is_exception_subclass(self):
        """Test that NotConnectedException inherits from Exception."""
        assert issubclass(NotConnectedException, Exception)

    def test_instantiation(self):
        """Test that NotConnectedException can be instantiated."""
        exc = NotConnectedException("Not connected")
        assert str(exc) == "Not connected"

    def test_raise_and_catch(self):
        """Test that NotConnectedException can be raised and caught."""
        with pytest.raises(NotConnectedException):
            raise NotConnectedException("Connection required")


class TestNotAuthenticatedException:
    """Tests for NotAuthenticatedException."""

    def test_is_exception_subclass(self):
        """Test that NotAuthenticatedException inherits from Exception."""
        assert issubclass(NotAuthenticatedException, Exception)

    def test_instantiation(self):
        """Test that NotAuthenticatedException can be instantiated."""
        exc = NotAuthenticatedException("Not authenticated")
        assert str(exc) == "Not authenticated"

    def test_raise_and_catch(self):
        """Test that NotAuthenticatedException can be raised and caught."""
        with pytest.raises(NotAuthenticatedException):
            raise NotAuthenticatedException("Authentication required")


class TestConnection:
    """Tests for the Connection base class."""

    def test_init_with_no_options(self):
        """Test Connection initialization without options."""
        conn = ConcreteConnection()
        assert conn.options == {"default_key": "default_value"}

    def test_init_with_options(self):
        """Test Connection initialization with custom options."""
        conn = ConcreteConnection(options={"custom_key": "custom_value"})
        # Default options should be present, custom options should be added
        assert conn.options["default_key"] == "default_value"
        assert conn.options["custom_key"] == "custom_value"

    def test_init_options_priority(self):
        """Test that default options take priority over passed options."""
        conn = ConcreteConnection(options={"default_key": "overridden"})
        # Default options should NOT be overridden (priority to defaults)
        assert conn.options["default_key"] == "default_value"

    def test_init_with_logger(self):
        """Test Connection initialization with custom logger."""
        mock_logger = MagicMock()
        conn = ConcreteConnection(logger=mock_logger)
        assert conn.logger == mock_logger

    def test_client_property_initially_none(self):
        """Test that client property is initially None."""
        conn = ConcreteConnection()
        assert conn.client is None

    def test_ready_property_initially_false(self):
        """Test that ready property is False before initialization."""
        conn = ConcreteConnection()
        assert conn.ready is False

    def test_ready_property_after_initialize(self):
        """Test that ready property is True after initialization."""
        conn = ConcreteConnection()
        conn.initialize()
        assert conn.ready is True

    def test_initialize_sets_initialized_flag(self):
        """Test that initialize() sets _initialized to True."""
        conn = ConcreteConnection()
        assert conn._initialized is False
        result = conn.initialize()
        assert result is True
        assert conn._initialized is True

    def test_check_valid_url(self):
        """Test check_valid_url method."""
        conn = ConcreteConnection()
        assert conn.check_valid_url("test://resource") is True
        assert conn.check_valid_url("invalid://resource") is False

    def test_get_resource_type(self):
        """Test get_resource_type method."""
        conn = ConcreteConnection()
        assert conn.get_resource_type("test://song/123") == ResourceType.SONG
        assert conn.get_resource_type("test://album/123") is None


class TestAuthenticatedConnection:
    """Tests for the AuthenticatedConnection class."""

    def test_init_with_no_options(self):
        """Test AuthenticatedConnection initialization without options."""
        conn = ConcreteAuthenticatedConnection()
        assert conn.options == {"auth_key": "auth_value"}

    def test_ready_initially_false(self):
        """Test that ready is False before initialization and authentication."""
        conn = ConcreteAuthenticatedConnection()
        assert conn.ready is False

    def test_ready_false_after_init_only(self):
        """Test that ready is False after initialization but before authentication."""
        conn = ConcreteAuthenticatedConnection()
        conn.initialize()
        assert conn._initialized is True
        assert conn._authenticated is False
        assert conn.ready is False

    def test_ready_false_after_auth_only(self):
        """Test that ready is False after authentication but before initialization."""
        conn = ConcreteAuthenticatedConnection()
        conn._authenticated = True  # Simulate auth without init
        assert conn._initialized is False
        assert conn._authenticated is True
        assert conn.ready is False

    def test_ready_true_after_init_and_auth(self):
        """Test that ready is True only after both initialization and authentication."""
        conn = ConcreteAuthenticatedConnection()
        conn.initialize()
        conn.authenticate()
        assert conn._initialized is True
        assert conn._authenticated is True
        assert conn.ready is True

    def test_authenticate_sets_authenticated_flag(self):
        """Test that authenticate() sets _authenticated to True."""
        conn = ConcreteAuthenticatedConnection()
        assert conn._authenticated is False
        result = conn.authenticate()
        assert result is True
        assert conn._authenticated is True


class TestRequireAuthentication:
    """Tests for the require_authentication decorator."""

    def test_decorator_allows_authenticated_call(self):
        """Test that decorated function executes when authenticated."""
        conn = ConcreteAuthenticatedConnection()
        conn.initialize()
        conn.authenticate()

        @conn.require_authentication
        def protected_function():
            return "success"

        result = protected_function()
        assert result == "success"

    def test_decorator_raises_when_not_authenticated(self):
        """Test that decorated function raises when not authenticated."""
        conn = ConcreteAuthenticatedConnection()
        conn.initialize()
        # Not calling authenticate()

        @conn.require_authentication
        def protected_function():
            return "success"

        with pytest.raises(NotAuthenticatedException):
            protected_function()

    def test_decorator_raises_when_not_initialized(self):
        """Test that decorated function raises when not initialized."""
        conn = ConcreteAuthenticatedConnection()
        conn._authenticated = True  # Simulate auth without init

        @conn.require_authentication
        def protected_function():
            return "success"

        with pytest.raises(NotAuthenticatedException):
            protected_function()

    def test_decorator_preserves_function_arguments(self):
        """Test that decorated function receives arguments correctly."""
        conn = ConcreteAuthenticatedConnection()
        conn.initialize()
        conn.authenticate()

        @conn.require_authentication
        def add_numbers(a, b):
            return a + b

        result = add_numbers(3, 5)
        assert result == 8

    def test_decorator_preserves_kwargs(self):
        """Test that decorated function receives keyword arguments correctly."""
        conn = ConcreteAuthenticatedConnection()
        conn.initialize()
        conn.authenticate()

        @conn.require_authentication
        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"

        result = greet("World", greeting="Hi")
        assert result == "Hi, World!"

    def test_decorator_error_message(self):
        """Test that the error message is correct."""
        conn = ConcreteAuthenticatedConnection()
        # Not initialized or authenticated

        @conn.require_authentication
        def protected_function():
            return "success"

        with pytest.raises(NotAuthenticatedException) as exc_info:
            protected_function()

        assert "requires authentication" in str(exc_info.value)
