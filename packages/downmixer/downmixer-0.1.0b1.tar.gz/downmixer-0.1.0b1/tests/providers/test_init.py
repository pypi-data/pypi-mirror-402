"""Unit types for the downmixer.providers module (discovery and base classes)."""

from typing import Protocol
from unittest.mock import MagicMock

import pytest

from downmixer.providers import (
    BaseProvider,
    ProviderInformation,
    get_all_providers_info,
    list_protocols,
    list_providers,
)
from downmixer.providers.connections import Connection
from downmixer.providers.protocols import (
    SupportsAudioDownload,
    SupportsLibrary,
    SupportsLyrics,
    SupportsMetadata,
)
from downmixer.types.library import ResourceType


class MockConnection(Connection):
    """Mock connection for testing BaseProvider."""

    _default_options = {"mock_option": "mock_value"}
    _initialized = True

    def initialize(self) -> bool:
        self._initialized = True
        return True

    def check_valid_url(self, url: str, type_filter=None) -> bool:
        return True

    def get_resource_type(self, value: str) -> ResourceType | None:
        return ResourceType.SONG


class TestBaseProvider:
    """Tests for the BaseProvider class."""

    def test_init_with_connection(self):
        """Test BaseProvider initialization with a connection."""
        conn = MockConnection()
        provider = BaseProvider(connection=conn)
        assert provider.connection == conn
        assert provider.client == conn.client

    def test_init_with_options(self):
        """Test BaseProvider initialization with custom options."""
        conn = MockConnection()
        provider = BaseProvider(connection=conn, options={"custom": "option"})
        assert provider.options["custom"] == "option"

    def test_init_with_logger(self):
        """Test BaseProvider initialization with custom logger."""
        conn = MockConnection()
        mock_logger = MagicMock()
        provider = BaseProvider(connection=conn, logger=mock_logger)
        assert provider.logger == mock_logger

    def test_name_property(self):
        """Test that name property returns _name."""

        class NamedProvider(BaseProvider):
            _name = "test_provider"

        conn = MockConnection()
        provider = NamedProvider(connection=conn)
        assert provider.name == "test_provider"

    def test_pretty_name_property(self):
        """Test that pretty_name property returns _pretty_name."""

        class NamedProvider(BaseProvider):
            _name = "test"
            _pretty_name = "Test Provider"

        conn = MockConnection()
        provider = NamedProvider(connection=conn)
        assert provider.pretty_name == "Test Provider"

    def test_name_with_whitespace_raises_error(self):
        """Test that a name with whitespace raises ValueError."""

        class BadProvider(BaseProvider):
            _name = "bad provider"

        conn = MockConnection()
        with pytest.raises(ValueError) as exc_info:
            BadProvider(connection=conn)

        assert "whitespace" in str(exc_info.value).lower()

    def test_name_with_spaces_raises_error(self):
        """Test various whitespace characters in name raise ValueError."""

        class TabProvider(BaseProvider):
            _name = "bad\tprovider"

        class NewlineProvider(BaseProvider):
            _name = "bad\nprovider"

        conn = MockConnection()

        with pytest.raises(ValueError):
            TabProvider(connection=conn)

        with pytest.raises(ValueError):
            NewlineProvider(connection=conn)

    def test_empty_name_is_valid(self):
        """Test that an empty name is valid (no whitespace)."""

        class EmptyNameProvider(BaseProvider):
            _name = ""

        conn = MockConnection()
        # Should not raise
        provider = EmptyNameProvider(connection=conn)
        assert provider.name == ""

    def test_options_merge_with_defaults(self):
        """Test that options are merged with default options."""

        class OptionsProvider(BaseProvider):
            _name = "options"
            _default_options = {"default": "value", "shared": "default"}

        conn = MockConnection()
        provider = OptionsProvider(
            connection=conn, options={"custom": "value", "shared": "custom"}
        )

        # Default options have priority
        assert provider.options["default"] == "value"
        assert provider.options["shared"] == "default"  # default wins
        assert provider.options["custom"] == "value"


class TestListProviders:
    """Tests for the list_providers() function."""

    def test_returns_list(self):
        """Test that list_providers returns a list."""
        result = list_providers()
        assert isinstance(result, list)

    def test_returns_provider_classes(self):
        """Test that list_providers returns BaseProvider subclasses."""
        result = list_providers()
        for provider_cls in result:
            # Each item should be a class (type)
            assert isinstance(provider_cls, type)

    def test_discovers_spotify_provider(self):
        """Test that Spotify provider is discovered."""
        result = list_providers()
        provider_names = [p._name for p in result]
        assert "spotify" in provider_names

    def test_discovers_multiple_providers(self):
        """Test that multiple providers are discovered."""
        result = list_providers()
        # At least Spotify, YTMusic, and Qobuz should be present
        assert len(result) >= 3


class TestListProtocols:
    """Tests for the list_protocols() function."""

    def test_returns_list(self):
        """Test that list_protocols returns a list."""
        result = list_protocols()
        assert isinstance(result, list)

    def test_returns_protocol_classes(self):
        """Test that list_protocols returns Protocol subclasses."""
        result = list_protocols()
        for protocol_cls in result:
            assert isinstance(protocol_cls, type)
            assert issubclass(protocol_cls, Protocol)

    def test_excludes_base_protocol(self):
        """Test that the base Protocol class is excluded."""
        result = list_protocols()
        assert Protocol not in result

    def test_includes_supports_metadata(self):
        """Test that SupportsMetadata is included."""
        result = list_protocols()
        assert SupportsMetadata in result

    def test_includes_supports_audio_download(self):
        """Test that SupportsAudioDownload is included."""
        result = list_protocols()
        assert SupportsAudioDownload in result

    def test_includes_supports_library(self):
        """Test that SupportsLibrary is included."""
        result = list_protocols()
        assert SupportsLibrary in result

    def test_includes_supports_lyrics(self):
        """Test that SupportsLyrics is included."""
        result = list_protocols()
        assert SupportsLyrics in result

    def test_returns_expected_count(self):
        """Test that the expected number of protocols is returned."""
        result = list_protocols()
        # We have 4 protocols defined
        assert len(result) == 4


class TestGetAllProvidersInfo:
    """Tests for the get_all_providers_info() function."""

    def test_returns_list(self):
        """Test that get_all_providers_info returns a list."""
        result = get_all_providers_info()
        assert isinstance(result, list)

    def test_list_contains_provider_information(self):
        """Test that list contains ProviderInformation instances."""
        result = get_all_providers_info()
        for item in result:
            assert isinstance(item, ProviderInformation)

    def test_provider_info_has_class_name(self):
        """Test that ProviderInformation has class_name attribute."""
        result = get_all_providers_info()
        for info in result:
            assert isinstance(info.class_name, str)
            assert len(info.class_name) > 0

    def test_provider_info_has_class_ref(self):
        """Test that ProviderInformation has class_ref attribute."""
        result = get_all_providers_info()
        for info in result:
            assert isinstance(info.class_ref, type)

    def test_provider_info_has_protocols_list(self):
        """Test that ProviderInformation has protocols list."""
        result = get_all_providers_info()
        for info in result:
            assert isinstance(info.protocols, list)
            for proto in info.protocols:
                assert isinstance(proto, type)
                assert issubclass(proto, Protocol)

    def test_provider_info_has_connections_list(self):
        """Test that ProviderInformation has connections list."""
        result = get_all_providers_info()
        for info in result:
            assert isinstance(info.connections, list)

    def test_discovers_multiple_providers(self):
        """Test that multiple providers are discovered."""
        result = get_all_providers_info()
        # At least Spotify, YTMusic, and Qobuz should be present
        assert len(result) >= 3
