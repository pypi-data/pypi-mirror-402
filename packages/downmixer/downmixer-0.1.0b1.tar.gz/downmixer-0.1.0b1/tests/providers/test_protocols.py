"""Unit types for the downmixer.providers.protocols module."""

from typing import Protocol

import pytest

from downmixer.providers.protocols import (
    SupportsAudioDownload,
    SupportsLibrary,
    SupportsLyrics,
    SupportsMetadata,
)
from downmixer.types.exceptions import IncompleteSupportWarning, UnsupportedException


class TestExceptions:
    """Tests for protocol exception classes."""

    def test_unsupported_exception_is_base_exception(self):
        """Test that UnsupportedException inherits from BaseException."""
        assert issubclass(UnsupportedException, BaseException)

    def test_unsupported_exception_instantiation(self):
        """Test that UnsupportedException can be instantiated."""
        exc = UnsupportedException("Feature not supported")
        assert str(exc) == "Feature not supported"

    def test_unsupported_exception_raise(self):
        """Test that UnsupportedException can be raised and caught."""
        with pytest.raises(UnsupportedException):
            raise UnsupportedException("Test error")

    def test_incomplete_support_warning_is_warning(self):
        """Test that IncompleteSupportWarning inherits from Warning."""
        assert issubclass(IncompleteSupportWarning, Warning)

    def test_incomplete_support_warning_instantiation(self):
        """Test that IncompleteSupportWarning can be instantiated."""
        warning = IncompleteSupportWarning("Partial support only")
        assert str(warning) == "Partial support only"


class TestSupportsMetadata:
    """Tests for the SupportsMetadata protocol."""

    def test_is_runtime_checkable(self):
        """Test that SupportsMetadata is runtime checkable."""
        assert hasattr(SupportsMetadata, "__protocol_attrs__") or hasattr(
            SupportsMetadata, "_is_runtime_protocol"
        )

    def test_is_protocol_subclass(self):
        """Test that SupportsMetadata is a Protocol."""
        assert issubclass(SupportsMetadata, Protocol)

    def test_required_methods_exist(self):
        """Test that SupportsMetadata defines required methods."""
        required_methods = [
            "search",
            "fetch_song",
            "fetch_album",
            "fetch_artist",
            "fetch_playlist",
            "fetch_user",
            "fetch_list_songs",
        ]
        for method in required_methods:
            assert hasattr(SupportsMetadata, method)

    def test_isinstance_check_with_compliant_class(self):
        """Test isinstance check with a class that implements the protocol."""

        class MockMetadataProvider:
            def search(self, query, accepted_types=None):
                return []

            def fetch_song(self, id):
                pass

            def fetch_album(self, id):
                pass

            def fetch_artist(self, id):
                pass

            def fetch_playlist(self, id):
                pass

            def fetch_user(self, id):
                pass

            def fetch_list_songs(self, id):
                return []

        provider = MockMetadataProvider()
        assert isinstance(provider, SupportsMetadata)

    def test_isinstance_check_with_non_compliant_class(self):
        """Test isinstance check with a class that doesn't implement the protocol."""

        class IncompleteProvider:
            def search(self, query):
                return []

        provider = IncompleteProvider()
        assert not isinstance(provider, SupportsMetadata)


class TestSupportsAudioDownload:
    """Tests for the SupportsAudioDownload protocol."""

    def test_is_runtime_checkable(self):
        """Test that SupportsAudioDownload is runtime checkable."""
        assert hasattr(SupportsAudioDownload, "__protocol_attrs__") or hasattr(
            SupportsAudioDownload, "_is_runtime_protocol"
        )

    def test_is_protocol_subclass(self):
        """Test that SupportsAudioDownload is a Protocol."""
        assert issubclass(SupportsAudioDownload, Protocol)

    def test_required_methods_exist(self):
        """Test that SupportsAudioDownload defines required methods."""
        required_methods = ["is_downloadable", "fetch_audio"]
        for method in required_methods:
            assert hasattr(SupportsAudioDownload, method)

    def test_isinstance_check_with_compliant_class(self):
        """Test isinstance check with a class that implements the protocol."""

        class MockAudioProvider:
            def is_downloadable(self, song):
                return True

            def fetch_audio(self, song, path):
                return None

        provider = MockAudioProvider()
        assert isinstance(provider, SupportsAudioDownload)


class TestSupportsLibrary:
    """Tests for the SupportsLibrary protocol."""

    def test_is_runtime_checkable(self):
        """Test that SupportsLibrary is runtime checkable."""
        assert hasattr(SupportsLibrary, "__protocol_attrs__") or hasattr(
            SupportsLibrary, "_is_runtime_protocol"
        )

    def test_is_protocol_subclass(self):
        """Test that SupportsLibrary is a Protocol."""
        assert issubclass(SupportsLibrary, Protocol)

    def test_required_methods_exist(self):
        """Test that SupportsLibrary defines required methods."""
        required_methods = [
            "fetch_user_playlists",
            "fetch_user_albums",
            "fetch_user_songs",
            "fetch_user_artists",
        ]
        for method in required_methods:
            assert hasattr(SupportsLibrary, method)

    def test_isinstance_check_with_compliant_class(self):
        """Test isinstance check with a class that implements the protocol."""

        class MockLibraryProvider:
            def fetch_user_playlists(self):
                return []

            def fetch_user_albums(self):
                return []

            def fetch_user_songs(self):
                return []

            def fetch_user_artists(self):
                return []

        provider = MockLibraryProvider()
        assert isinstance(provider, SupportsLibrary)


class TestSupportsLyrics:
    """Tests for the SupportsLyrics protocol."""

    def test_is_runtime_checkable(self):
        """Test that SupportsLyrics is runtime checkable."""
        assert hasattr(SupportsLyrics, "__protocol_attrs__") or hasattr(
            SupportsLyrics, "_is_runtime_protocol"
        )

    def test_is_protocol_subclass(self):
        """Test that SupportsLyrics is a Protocol."""
        assert issubclass(SupportsLyrics, Protocol)

    def test_required_methods_exist(self):
        """Test that SupportsLyrics defines required methods."""
        required_methods = ["fetch_lyrics", "list_supported_languages"]
        for method in required_methods:
            assert hasattr(SupportsLyrics, method)

    def test_isinstance_check_with_compliant_class(self):
        """Test isinstance check with a class that implements the protocol."""

        class MockLyricsProvider:
            def fetch_lyrics(self, song):
                return "Lyrics here"

            def list_supported_languages(self):
                return ["en", "es"]

        provider = MockLyricsProvider()
        assert isinstance(provider, SupportsLyrics)
