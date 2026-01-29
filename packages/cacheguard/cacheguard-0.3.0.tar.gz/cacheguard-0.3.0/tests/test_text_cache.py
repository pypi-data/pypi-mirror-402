"""
Tests for the TextCache class
"""

from unittest.mock import mock_open, patch

from pytest import fixture, mark

# Local Testing Library
from test_common import (
    decrypt_params,
    encrypt_params,
    set_age_env_var,  # noqa - this is a fixture
)

from cacheguard.text_cache import TextCache


class TestTextCache:
    """Test cases for TextCache functionality"""

    @fixture
    def temp_path(self, tmp_path):
        """Create a temporary file path for testing"""
        return tmp_path / "test_cache.txt"

    @fixture
    def sample_data(self):
        """Sample text data for testing"""
        return "line1\nline2\nline3"

    @fixture
    def encrypted_data(self):
        """Sample encrypted data"""
        return "encrypted_content_here"

    def test_init_no_existing_file(self, temp_path):
        """Test initialization when cache file doesn't exist"""
        with patch("cacheguard.base_cache.path.exists", return_value=False):
            cache = TextCache(str(temp_path))
            assert cache.age_pubkeys == []  # nosec B101
            assert cache.pgp_fingerprints == []  # nosec B101
            assert cache.cache_path == str(temp_path)  # nosec B101
            assert cache.newline == "\n"  # nosec B101
            assert cache.buffer.getvalue() == ""  # nosec B101

    @mark.parametrize("backend,decrypt_patch", decrypt_params())
    def test_init_with_existing_file(
        self, temp_path, sample_data, backend, decrypt_patch
    ):
        """Test initialization when cache file exists"""
        with (
            patch("cacheguard.base_cache.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data="dummy")),
            patch(decrypt_patch, return_value=sample_data),
        ):
            cache = TextCache(str(temp_path), backend=backend)
            assert cache.age_pubkeys == []  # nosec B101
            assert cache.pgp_fingerprints == []  # nosec B101
            assert cache.cache_path == str(temp_path)  # nosec B101
            assert cache.newline == "\n"  # nosec B101
            # Should have appended the lines
            expected = "line1\nline2\nline3\n"
            assert cache.buffer.getvalue() == expected  # nosec B101

    @mark.parametrize("backend,decrypt_patch", decrypt_params())
    def test_init_custom_newline(self, temp_path, sample_data, backend, decrypt_patch):
        """Test initialization with custom newline"""
        custom_newline = "\r\n"
        sample_data_custom = "line1\r\nline2\r\nline3"
        with (
            patch("cacheguard.base_cache.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data="dummy")),
            patch(decrypt_patch, return_value=sample_data_custom),
        ):
            cache = TextCache(str(temp_path), newline=custom_newline, backend=backend)
            assert cache.newline == custom_newline  # nosec B101
            expected = "line1\r\nline2\r\nline3\r\n"
            assert cache.buffer.getvalue() == expected  # nosec B101

    @mark.parametrize("backend,decrypt_patch", decrypt_params())
    def test_load(self, temp_path, sample_data, backend, decrypt_patch):
        """Test load method"""
        cache = TextCache(str(temp_path), backend=backend)
        with (
            patch("builtins.open", mock_open(read_data="encrypted")),
            patch(decrypt_patch, return_value=sample_data),
        ):
            result = cache.load()
            assert result == sample_data  # nosec B101
            # Buffer should be reset to StringIO with data
            assert cache.buffer.getvalue() == sample_data  # nosec B101

    @mark.parametrize("backend,encrypt_patch", encrypt_params())
    def test_save_without_data_string(
        self, temp_path, encrypted_data, backend, encrypt_patch
    ):
        """Test save method without providing data_string"""
        cache = TextCache(str(temp_path), backend=backend)
        cache.buffer.write("test content\nmore content\n")

        with (
            patch(encrypt_patch, return_value=encrypted_data),
            patch("cacheguard.base_cache.path.exists", return_value=True),
            patch("builtins.open", mock_open()),
        ):
            cache.save()

            # Should encrypt the buffer content stripped
            expected_data = "test content\nmore content"
            # Verify encrypt was called with stripped buffer content
            # Since we can't easily check the call, check that save was called on super
            # Actually, patch super().save
            with patch("cacheguard.base_cache.BaseCache.save") as mock_super_save:
                cache.save()
                mock_super_save.assert_called_with(expected_data)

    def test_save_with_data_string(self, temp_path, sample_data, encrypted_data):
        """Test save method with provided data_string"""
        cache = TextCache(str(temp_path))

        with patch("cacheguard.base_cache.BaseCache.save") as mock_super_save:
            cache.save(sample_data)
            mock_super_save.assert_called_with(sample_data)

    def test_append(self, temp_path):
        """Test append method"""
        cache = TextCache(str(temp_path))
        cache.append("first line")
        cache.append("second line")
        expected = "first line\nsecond line\n"
        assert cache.buffer.getvalue() == expected  # nosec B101

    def test_append_custom_newline(self, temp_path):
        """Test append with custom newline"""
        cache = TextCache(str(temp_path), newline="\r\n")
        cache.append("first line")
        cache.append("second line")
        expected = "first line\r\nsecond line\r\n"
        assert cache.buffer.getvalue() == expected  # nosec B101
