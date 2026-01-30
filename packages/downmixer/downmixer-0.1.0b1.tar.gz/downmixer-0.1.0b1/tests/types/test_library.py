"""Unit types for the downmixer.types.library module."""

from downmixer.types.library import (
    Album,
    AlbumType,
    Artist,
    BaseLibraryItem,
    Playlist,
    ResourceType,
    Song,
    User,
)


class TestResourceType:
    """Tests for ResourceType enum."""

    def test_resource_types_exist(self):
        """Test that all expected resource types exist."""
        assert ResourceType.SONG
        assert ResourceType.ALBUM
        assert ResourceType.ARTIST
        assert ResourceType.PLAYLIST
        assert ResourceType.USER
        assert ResourceType.UNKNOWN


class TestAlbumType:
    """Tests for AlbumType enum."""

    def test_album_types_exist(self):
        """Test that all expected album types exist."""
        assert AlbumType.ALBUM
        assert AlbumType.SINGLE
        assert AlbumType.COMPILATION


class TestArtist:
    """Tests for the Artist dataclass."""

    def test_artist_creation(self):
        """Test basic Artist creation."""
        artist = Artist(name="Test Artist")
        assert artist.name == "Test Artist"
        assert artist.id is None
        assert artist.images is None

    def test_artist_with_all_fields(self, sample_artist: Artist):
        """Test Artist creation with all fields."""
        assert sample_artist.name == "Test Artist"
        assert sample_artist.id == "artist123"
        assert sample_artist.images == ["https://example.com/image.jpg"]
        assert sample_artist.genres == ["rock", "indie"]
        assert sample_artist.url == "https://example.com/artist"

    def test_artist_slug(self, sample_artist: Artist):
        """Test Artist.slug() method slugifies text attributes."""
        slugged = sample_artist.slug()
        assert slugged.name == "test-artist"
        assert slugged.genres == ["rock", "indie"]
        assert slugged.id == sample_artist.id  # ID should remain unchanged

    def test_artist_slug_with_special_chars(self):
        """Test Artist.slug() handles special characters."""
        artist = Artist(name="Test Artist!@#$%", genres=["Rock & Roll", "Pop-Punk"])
        slugged = artist.slug()
        assert slugged.name == "test-artist"
        assert "rock-roll" in slugged.genres or "rock-and-roll" in slugged.genres

    def test_artist_slug_none_genres(self):
        """Test Artist.slug() handles None genres."""
        artist = Artist(name="Test Artist", genres=None)
        slugged = artist.slug()
        assert slugged.genres is None

    def test_artist_from_dict(self):
        """Test Artist.from_dict() creates instance correctly."""
        data = {
            "name": "Dict Artist",
            "images": ["img1.jpg"],
            "genres": ["jazz"],
            "id": "dict_id",
            "url": "https://example.com",
        }
        artist = Artist.from_dict(data)
        assert artist.name == "Dict Artist"
        assert artist.id == "dict_id"
        assert artist.genres == ["jazz"]

    def test_artist_from_dict_empty(self):
        """Test Artist.from_dict() with empty dict."""
        artist = Artist.from_dict({})
        assert artist.name is None
        assert artist.id is None

    def test_artist_to_dict(self, sample_artist: Artist):
        """Test Artist.to_dict() converts to dictionary."""
        result = sample_artist.to_dict()
        assert result["name"] == "Test Artist"
        assert result["id"] == "artist123"
        assert result["genres"] == ["rock", "indie"]
        assert result["images"] == ["https://example.com/image.jpg"]

    def test_artist_hash_with_id(self, sample_artist: Artist):
        """Test Artist hash uses id when available."""
        hash1 = hash(sample_artist)
        hash2 = hash(sample_artist)
        assert hash1 == hash2
        assert hash1 == hash("artist123")

    def test_artist_hash_without_id(self):
        """Test Artist hash uses name when id is None."""
        artist = Artist(name="No ID Artist")
        assert hash(artist) == hash("No ID Artist")

    def test_artist_str(self, sample_artist: Artist):
        """Test Artist string representation."""
        assert str(sample_artist) == "Test Artist"

    def test_artist_resource_type(self):
        """Test Artist has correct resource type."""
        assert Artist.get_resource_type() == ResourceType.ARTIST


class TestAlbum:
    """Tests for the Album dataclass."""

    def test_album_creation(self, sample_artist: Artist):
        """Test basic Album creation."""
        album = Album(name="Test Album", artists=[sample_artist])
        assert album.name == "Test Album"
        assert len(album.artists) == 1

    def test_album_with_all_fields(self, sample_album: Album):
        """Test Album creation with all fields."""
        assert sample_album.name == "Test Album"
        assert sample_album.id == "album123"
        assert sample_album.track_count == 12
        assert sample_album.date == "2024-01-15"

    def test_album_title_property(self, sample_album: Album):
        """Test Album.title property."""
        assert sample_album.title == "Test Artist - Test Album"

    def test_album_full_title_property(self, sample_album: Album):
        """Test Album.full_title property."""
        assert sample_album.full_title == "Test Artist - Test Album"

    def test_album_full_title_multiple_artists(
        self, sample_artist: Artist, sample_artist_2: Artist
    ):
        """Test Album.full_title with multiple artists."""
        album = Album(name="Collab Album", artists=[sample_artist, sample_artist_2])
        assert album.full_title == "Test Artist, Another Artist - Collab Album"

    def test_album_all_artists_property(
        self, sample_artist: Artist, sample_artist_2: Artist
    ):
        """Test Album.all_artists property."""
        album = Album(name="Test", artists=[sample_artist, sample_artist_2])
        assert album.all_artists == "Test Artist, Another Artist"

    def test_album_slug(self, sample_album: Album):
        """Test Album.slug() method."""
        slugged = sample_album.slug()
        assert slugged.name == "test-album"
        assert slugged.id == sample_album.id

    def test_album_from_dict(self):
        """Test Album.from_dict() creates instance correctly."""
        data = {
            "name": "Dict Album",
            "artists": [{"name": "Artist1", "id": "a1"}],
            "date": "2024-01-01",
            "track_count": 10,
            "id": "album_dict",
        }
        album = Album.from_dict(data)
        assert album.name == "Dict Album"
        assert album.id == "album_dict"
        assert len(album.artists) == 1
        assert album.artists[0].name == "Artist1"

    def test_album_from_dict_no_artists(self):
        """Test Album.from_dict() with no artists."""
        data = {"name": "Solo Album"}
        album = Album.from_dict(data)
        assert album.name == "Solo Album"
        assert album.artists == []

    def test_album_to_dict(self, sample_album: Album):
        """Test Album.to_dict() converts to dictionary."""
        result = sample_album.to_dict()
        assert result["name"] == "Test Album"
        assert result["id"] == "album123"
        assert len(result["artists"]) == 1
        assert result["artists"][0]["name"] == "Test Artist"

    def test_album_hash_with_id(self, sample_album: Album):
        """Test Album hash uses id when available."""
        assert hash(sample_album) == hash("album123")

    def test_album_hash_without_id(self, sample_artist: Artist):
        """Test Album hash uses full_title when id is None."""
        album = Album(name="No ID Album", artists=[sample_artist])
        assert hash(album) == hash(album.full_title)

    def test_album_str(self, sample_album: Album):
        """Test Album string representation."""
        assert str(sample_album) == "Test Artist - Test Album"

    def test_album_resource_type(self):
        """Test Album has correct resource type."""
        assert Album.get_resource_type() == ResourceType.ALBUM


class TestSong:
    """Tests for the Song dataclass."""

    def test_song_creation(self, sample_artist: Artist):
        """Test basic Song creation."""
        song = Song(name="Test Song", artists=[sample_artist])
        assert song.name == "Test Song"
        assert song.duration == 0

    def test_song_with_all_fields(self, sample_song: Song):
        """Test Song creation with all fields."""
        assert sample_song.name == "Test Song"
        assert sample_song.id == "song123"
        assert sample_song.duration == 210.5
        assert sample_song.isrc == "USRC12345678"
        assert sample_song.lyrics == "Test lyrics here"

    def test_song_title_property(self, sample_song: Song):
        """Test Song.title property."""
        assert sample_song.title == "Test Artist - Test Song"

    def test_song_full_title_property(self, sample_song: Song):
        """Test Song.full_title property."""
        assert sample_song.full_title == "Test Artist - Test Song"

    def test_song_full_title_multiple_artists(self, sample_song_multiple_artists: Song):
        """Test Song.full_title with multiple artists."""
        assert (
            sample_song_multiple_artists.full_title
            == "Test Artist, Another Artist - Collaboration Song"
        )

    def test_song_all_artists_property(self, sample_song_multiple_artists: Song):
        """Test Song.all_artists property."""
        assert sample_song_multiple_artists.all_artists == "Test Artist, Another Artist"

    def test_song_slug(self, sample_song: Song):
        """Test Song.slug() method."""
        slugged = sample_song.slug()
        assert slugged.name == "test-song"
        assert slugged.id == sample_song.id
        assert slugged.duration == sample_song.duration

    def test_song_slug_with_lyrics(self, sample_song: Song):
        """Test Song.slug() slugifies lyrics."""
        slugged = sample_song.slug()
        assert slugged.lyrics == "test-lyrics-here"

    def test_song_slug_without_album(self, sample_artist: Artist):
        """Test Song.slug() handles None album."""
        song = Song(name="No Album Song", artists=[sample_artist])
        slugged = song.slug()
        assert slugged.album is None

    def test_song_from_dict(self):
        """Test Song.from_dict() creates instance correctly."""
        data = {
            "name": "Dict Song",
            "artists": [{"name": "Artist1", "id": "a1"}],
            "duration": 180.0,
            "album": {"name": "Album1", "artists": [{"name": "Artist1"}]},
            "id": "song_dict",
            "isrc": "USTEST123",
        }
        song = Song.from_dict(data)
        assert song.name == "Dict Song"
        assert song.id == "song_dict"
        assert song.duration == 180.0
        assert song.album.name == "Album1"

    def test_song_from_dict_minimal(self):
        """Test Song.from_dict() with minimal data."""
        data = {"name": "Minimal Song"}
        song = Song.from_dict(data)
        assert song.name == "Minimal Song"
        assert song.artists == []
        assert song.duration == 0
        assert song.album is None

    def test_song_to_dict_full(self, sample_song: Song):
        """Test Song.to_dict() with full data."""
        result = sample_song.to_dict(minimal=False)
        assert result["name"] == "Test Song"
        assert result["id"] == "song123"
        assert result["duration"] == 210.5
        assert result["lyrics"] == "Test lyrics here"
        assert result["album"]["name"] == "Test Album"

    def test_song_to_dict_minimal(self, sample_song: Song):
        """Test Song.to_dict() with minimal data."""
        result = sample_song.to_dict(minimal=True)
        assert result["name"] == "Test Song"
        assert result["id"] == "song123"
        assert result["isrc"] == "USRC12345678"
        assert "duration" not in result
        assert "lyrics" not in result

    def test_song_hash_with_id(self, sample_song: Song):
        """Test Song hash uses id when available."""
        assert hash(sample_song) == hash("song123")

    def test_song_hash_without_id(self, sample_artist: Artist):
        """Test Song hash uses full_title when id is None."""
        song = Song(name="No ID Song", artists=[sample_artist])
        assert hash(song) == hash(song.full_title)

    def test_song_str(self, sample_song: Song):
        """Test Song string representation."""
        assert str(sample_song) == "Test Artist - Test Song"

    def test_song_resource_type(self):
        """Test Song has correct resource type."""
        assert Song.get_resource_type() == ResourceType.SONG


class TestUser:
    """Tests for the User dataclass."""

    def test_user_creation(self):
        """Test basic User creation."""
        user = User(id="user123", name="Test User")
        assert user.id == "user123"
        assert user.name == "Test User"

    def test_user_with_handle(self):
        """Test User creation with handle."""
        user = User(id="user123", name="Test User", handle="@testuser")
        assert user.handle == "@testuser"

    def test_user_hash_with_id(self):
        """Test User hash uses id when available."""
        user = User(id="user123", name="Test User")
        assert hash(user) == hash("user123")

    def test_user_hash_with_handle_no_id(self):
        """Test User hash uses handle when id is None."""
        user = User(name="Test User", handle="@testuser")
        assert hash(user) == hash("@testuser")

    def test_user_hash_with_name_only(self):
        """Test User hash uses name as fallback."""
        user = User(name="Test User")
        assert hash(user) == hash("Test User")

    def test_user_str_with_name(self):
        """Test User string representation with name."""
        user = User(id="user123", name="Test User")
        assert str(user) == "Test User (user123)"

    def test_user_str_without_name(self):
        """Test User string representation without name."""
        user = User(id="user123")
        assert str(user) == "user123"

    def test_user_resource_type(self):
        """Test User has correct resource type."""
        assert User.get_resource_type() == ResourceType.USER


class TestPlaylist:
    """Tests for the Playlist dataclass."""

    def test_playlist_creation(self):
        """Test basic Playlist creation."""
        playlist = Playlist(name="Test Playlist")
        assert playlist.name == "Test Playlist"
        assert playlist.tracks is None

    def test_playlist_with_owner(self):
        """Test Playlist creation with owner."""
        owner = User(id="owner1", name="Owner User")
        playlist = Playlist(name="Test Playlist", owner=owner)
        assert playlist.owner.name == "Owner User"

    def test_playlist_with_tracks(self, sample_song: Song):
        """Test Playlist creation with tracks."""
        playlist = Playlist(name="Test Playlist", tracks=[sample_song])
        assert len(playlist.tracks) == 1
        assert playlist.tracks[0].name == "Test Song"

    def test_playlist_title_with_owner(self):
        """Test Playlist.title property with owner."""
        owner = User(id="owner1", name="Owner User")
        playlist = Playlist(name="Test Playlist", owner=owner)
        assert playlist.title == "Test Playlist by Owner User"

    def test_playlist_title_without_owner(self):
        """Test Playlist.title property without owner."""
        playlist = Playlist(name="Test Playlist")
        assert playlist.title == "Test Playlist by Unknown"

    def test_playlist_hash_with_id(self):
        """Test Playlist hash uses id when available."""
        playlist = Playlist(name="Test", id="playlist123")
        assert hash(playlist) == hash("playlist123")

    def test_playlist_hash_without_id(self):
        """Test Playlist hash uses title when id is None."""
        owner = User(name="Owner")
        playlist = Playlist(name="Test Playlist", owner=owner)
        assert hash(playlist) == hash(playlist.title)

    def test_playlist_str(self):
        """Test Playlist string representation."""
        owner = User(name="Owner")
        playlist = Playlist(name="Test Playlist", owner=owner)
        assert str(playlist) == "Test Playlist by Owner"

    def test_playlist_resource_type(self):
        """Test Playlist has correct resource type."""
        assert Playlist.get_resource_type() == ResourceType.PLAYLIST


class TestBaseLibraryItem:
    """Tests for the BaseLibraryItem base class."""

    def test_from_provider_list(self):
        """Test from_provider_list creates multiple instances."""

        class MockItem(BaseLibraryItem):
            def __init__(self, value):
                self.value = value

            @classmethod
            def from_provider(cls, data, extra_data=None):
                return cls(value=data.get("value"))

        data_list = [{"value": 1}, {"value": 2}, {"value": 3}]
        items = MockItem.from_provider_list(data_list)
        assert len(items) == 3
        assert items[0].value == 1
        assert items[2].value == 3
