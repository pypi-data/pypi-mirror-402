"""Unit types for the downmixer.file_tools.utils module."""

from downmixer.file_tools.utils import make_sane_filename


class TestMakeSaneFilename:
    """Tests for the make_sane_filename function."""

    def test_normal_filename(self):
        """Test that normal filenames are unchanged."""
        filename = "normal_filename.mp3"
        result = make_sane_filename(filename)
        assert result == "normal_filename.mp3"

    def test_removes_forward_slash(self):
        """Test that forward slashes are replaced."""
        filename = "path/to/file.mp3"
        result = make_sane_filename(filename)
        assert "/" not in result
        assert result == "path-to-file.mp3"

    def test_removes_backslash(self):
        """Test that backslashes are replaced."""
        filename = "path\\to\\file.mp3"
        result = make_sane_filename(filename)
        assert "\\" not in result
        assert result == "path-to-file.mp3"

    def test_removes_question_mark(self):
        """Test that question marks are replaced."""
        filename = "what?why?.mp3"
        result = make_sane_filename(filename)
        assert "?" not in result
        assert result == "what-why-.mp3"

    def test_removes_percent(self):
        """Test that percent signs are replaced."""
        filename = "100%music.mp3"
        result = make_sane_filename(filename)
        assert "%" not in result
        assert result == "100-music.mp3"

    def test_removes_asterisk(self):
        """Test that asterisks are replaced."""
        filename = "star*song*.mp3"
        result = make_sane_filename(filename)
        assert "*" not in result
        assert result == "star-song-.mp3"

    def test_removes_colon(self):
        """Test that colons are replaced."""
        filename = "Artist: Song Name.mp3"
        result = make_sane_filename(filename)
        assert ":" not in result
        assert result == "Artist- Song Name.mp3"

    def test_removes_pipe(self):
        """Test that pipe characters are replaced."""
        filename = "Artist | Song.mp3"
        result = make_sane_filename(filename)
        assert "|" not in result
        assert result == "Artist - Song.mp3"

    def test_removes_double_quotes(self):
        """Test that double quotes are replaced."""
        filename = '"Quoted" Title.mp3'
        result = make_sane_filename(filename)
        assert '"' not in result
        assert result == "-Quoted- Title.mp3"

    def test_removes_angle_brackets(self):
        """Test that angle brackets are replaced."""
        filename = "<artist> - <song>.mp3"
        result = make_sane_filename(filename)
        assert "<" not in result
        assert ">" not in result
        assert result == "-artist- - -song-.mp3"

    def test_removes_control_characters(self):
        """Test that control characters (0x00-0x1F) are replaced."""
        filename = "test\x00file\x1fname.mp3"
        result = make_sane_filename(filename)
        assert "\x00" not in result
        assert "\x1f" not in result
        assert result == "test-file-name.mp3"

    def test_removes_del_character(self):
        """Test that DEL character (0x7F) is replaced."""
        filename = "test\x7ffile.mp3"
        result = make_sane_filename(filename)
        assert "\x7f" not in result
        assert result == "test-file.mp3"

    def test_multiple_illegal_characters(self):
        """Test handling multiple illegal characters in sequence."""
        filename = "Artist???Song***.mp3"
        result = make_sane_filename(filename)
        assert result == "Artist---Song---.mp3"

    def test_all_illegal_characters_combined(self):
        """Test a filename with all illegal characters."""
        filename = '/\\?%*:|"<>'
        result = make_sane_filename(filename)
        assert result == "----------"

    def test_preserves_valid_special_characters(self):
        """Test that valid special characters are preserved."""
        filename = "Artist - Song (feat. Other) [Remix].mp3"
        result = make_sane_filename(filename)
        assert result == "Artist - Song (feat. Other) [Remix].mp3"

    def test_preserves_unicode_characters(self):
        """Test that unicode characters are preserved."""
        filename = "アーティスト - 曲名.mp3"
        result = make_sane_filename(filename)
        assert result == "アーティスト - 曲名.mp3"

    def test_preserves_accented_characters(self):
        """Test that accented characters are preserved."""
        filename = "Café résumé naïve.mp3"
        result = make_sane_filename(filename)
        assert result == "Café résumé naïve.mp3"

    def test_preserves_emoji(self):
        """Test that emoji are preserved."""
        filename = "🎵 Song 🎸.mp3"
        result = make_sane_filename(filename)
        assert result == "🎵 Song 🎸.mp3"

    def test_empty_string(self):
        """Test handling of empty string."""
        result = make_sane_filename("")
        assert result == ""

    def test_only_illegal_characters(self):
        """Test a filename with only illegal characters."""
        filename = "???***"
        result = make_sane_filename(filename)
        assert result == "------"

    def test_spaces_preserved(self):
        """Test that spaces are preserved."""
        filename = "Artist   -   Song.mp3"
        result = make_sane_filename(filename)
        assert result == "Artist   -   Song.mp3"

    def test_dots_preserved(self):
        """Test that dots are preserved."""
        filename = "artist.name.song.mp3"
        result = make_sane_filename(filename)
        assert result == "artist.name.song.mp3"

    def test_underscores_preserved(self):
        """Test that underscores are preserved."""
        filename = "artist_name_song.mp3"
        result = make_sane_filename(filename)
        assert result == "artist_name_song.mp3"

    def test_hyphens_preserved(self):
        """Test that hyphens are preserved."""
        filename = "artist-name-song.mp3"
        result = make_sane_filename(filename)
        assert result == "artist-name-song.mp3"

    def test_numbers_preserved(self):
        """Test that numbers are preserved."""
        filename = "01 - Track 01.mp3"
        result = make_sane_filename(filename)
        assert result == "01 - Track 01.mp3"

    def test_real_world_example_1(self):
        """Test real-world filename with colons and question marks."""
        filename = "Artist: What Is Love? (Radio Edit).mp3"
        result = make_sane_filename(filename)
        assert result == "Artist- What Is Love- (Radio Edit).mp3"

    def test_real_world_example_2(self):
        """Test real-world filename with angle brackets."""
        filename = "<Unknown Artist> - <Unknown Song>.mp3"
        result = make_sane_filename(filename)
        assert result == "-Unknown Artist- - -Unknown Song-.mp3"

    def test_real_world_example_3(self):
        """Test real-world filename with pipes for featuring."""
        filename = "Main Artist | Feat. Other Artist.mp3"
        result = make_sane_filename(filename)
        assert result == "Main Artist - Feat. Other Artist.mp3"
