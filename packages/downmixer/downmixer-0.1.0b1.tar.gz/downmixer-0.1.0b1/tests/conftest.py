"""Shared pytest fixtures for all types."""

import pytest

from downmixer.types.library import Album, Artist, Song


@pytest.fixture
def sample_artist() -> Artist:
    """Create a sample Artist for testing."""
    return Artist(
        name="Test Artist",
        images=["https://example.com/image.jpg"],
        genres=["rock", "indie"],
        id="artist123",
        url="https://example.com/artist",
    )


@pytest.fixture
def sample_artist_2() -> Artist:
    """Create a second sample Artist for testing."""
    return Artist(
        name="Another Artist",
        images=["https://example.com/image2.jpg"],
        genres=["pop"],
        id="artist456",
        url="https://example.com/artist2",
    )


@pytest.fixture
def sample_album(sample_artist: Artist) -> Album:
    """Create a sample Album for testing."""
    return Album(
        name="Test Album",
        available_markets=["US", "GB"],
        artists=[sample_artist],
        date="2024-01-15",
        track_count=12,
        cover="https://example.com/cover.jpg",
        upc="123456789012",
        id="album123",
        url="https://example.com/album",
    )


@pytest.fixture
def sample_song(sample_artist: Artist, sample_album: Album) -> Song:
    """Create a sample Song for testing."""
    return Song(
        name="Test Song",
        artists=[sample_artist],
        duration=210.5,
        album=sample_album,
        available_markets=["US", "GB"],
        date="2024-01-15",
        track_number=1,
        isrc="USRC12345678",
        lyrics="Test lyrics here",
        id="song123",
        url="https://example.com/song",
        cover="https://example.com/cover.jpg",
    )


@pytest.fixture
def sample_song_multiple_artists(
    sample_artist: Artist, sample_artist_2: Artist, sample_album: Album
) -> Song:
    """Create a sample Song with multiple artists for testing."""
    return Song(
        name="Collaboration Song",
        artists=[sample_artist, sample_artist_2],
        duration=180.0,
        album=sample_album,
        available_markets=["US"],
        date="2024-02-01",
        track_number=5,
        isrc="USRC98765432",
        id="song456",
        url="https://example.com/song2",
    )


@pytest.fixture
def similar_song(sample_artist: Artist, sample_album: Album) -> Song:
    """Create a song similar to sample_song for matching types."""
    return Song(
        name="Test Song",
        artists=[sample_artist],
        duration=211.0,
        album=sample_album,
        id="song_similar",
    )


@pytest.fixture
def different_song() -> Song:
    """Create a completely different song for matching types."""
    different_artist = Artist(name="Different Artist", id="different_artist")
    different_album = Album(name="Different Album", artists=[different_artist])
    return Song(
        name="Completely Different Song",
        artists=[different_artist],
        duration=300.0,
        album=different_album,
        id="song_different",
    )
