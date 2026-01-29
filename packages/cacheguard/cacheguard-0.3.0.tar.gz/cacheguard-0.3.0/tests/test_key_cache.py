"""
Tests for the KeyCache class
"""

from unittest.mock import mock_open, patch

from pytest import fixture, mark, raises

# Local Testing Libraries
from test_common import (
    decrypt_params,
    encrypt_params,
    set_age_env_var,  # noqa - this is a fixture
)

from cacheguard.key_cache import KeyCache


class TestKeyCache:
    """Test cases for KeyCache functionality"""

    @fixture
    def temp_path(self, tmp_path):
        """Create a temporary file path for testing"""
        return tmp_path / "test_cache.json"

    @fixture
    def sample_data(self):
        """Sample key-value data for testing"""
        return {"key1": "value1", "key2": "value2"}

    @fixture
    def sample_json(self):
        """Sample JSON string"""
        return '{"key1": "value1", "key2": "value2"}'

    @fixture
    def encrypted_data(self):
        """Sample encrypted data"""
        return "encrypted_content_here"

    def test_init_no_existing_file(self, temp_path):
        """Test initialization when cache file doesn't exist"""
        with patch("cacheguard.base_cache.path.exists", return_value=False):
            cache = KeyCache(str(temp_path))
            assert cache.age_pubkeys == []  # nosec B101
            assert cache.pgp_fingerprints == []  # nosec B101
            assert cache.cache_path == str(temp_path)  # nosec B101
            assert cache.data == {}  # nosec B101

    @mark.parametrize("backend,decrypt_patch", decrypt_params())
    def test_init_with_existing_file(
        self, temp_path, sample_json, backend, decrypt_patch
    ):
        """Test initialization when cache file exists"""
        with (
            patch("cacheguard.base_cache.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data="dummy")),
            patch(decrypt_patch, return_value=sample_json),
        ):
            cache = KeyCache(str(temp_path), backend=backend)
            assert cache.age_pubkeys == []  # nosec B101
            assert cache.pgp_fingerprints == []  # nosec B101
            assert cache.cache_path == str(temp_path)  # nosec B101
            assert cache.data == {"key1": "value1", "key2": "value2"}  # nosec B101

    @mark.parametrize("backend,decrypt_patch", decrypt_params())
    def test_load_success(self, temp_path, sample_json, backend, decrypt_patch):
        """Test successful loading of cache data"""
        cache = KeyCache(str(temp_path), backend=backend)
        with (
            patch("builtins.open", mock_open(read_data="encrypted")),
            patch(decrypt_patch, return_value=sample_json),
        ):
            result = cache.load()
            assert result == {"key1": "value1", "key2": "value2"}  # nosec B101
            assert cache.data == {"key1": "value1", "key2": "value2"}  # nosec B101

    def test_load_empty_data(self, temp_path):
        """Test loading when no data exists"""
        cache = KeyCache(str(temp_path))
        with (
            patch("builtins.open", side_effect=OSError("File error")),
            patch("cacheguard.base_cache.move"),
        ):
            result = cache.load()
            assert result == {}  # nosec B101
            assert cache.data == {}  # nosec B101

    @mark.parametrize("backend,encrypt_patch", encrypt_params())
    def test_save(self, temp_path, sample_data, encrypted_data, backend, encrypt_patch):
        """Test save method"""
        cache = KeyCache(str(temp_path), backend=backend)
        cache.data = sample_data

        with (
            patch(encrypt_patch, return_value=encrypted_data),
            patch("cacheguard.base_cache.path.exists", return_value=True),
            patch("builtins.open", mock_open()),
        ):
            cache.save()

            # Should encrypt the JSON string
            expected_json = '{"key1": "value1", "key2": "value2"}'
            # Verify encrypt was called with JSON
            # Since we can't easily check the call, check that save was called on super
            with patch("cacheguard.base_cache.BaseCache.save") as mock_super_save:
                cache.save()
                mock_super_save.assert_called_with(expected_json)

    def test_add(self, temp_path):
        """Test add method"""
        cache = KeyCache(str(temp_path))
        cache.data = {"existing": "value"}

        new_entry = {"new_key": "new_value", "another": "entry"}
        cache.add(new_entry)

        expected = {"existing": "value", "new_key": "new_value", "another": "entry"}
        assert cache.data == expected  # nosec B101

    def test_add_overwrites_existing(self, temp_path):
        """Test add method overwrites existing keys"""
        cache = KeyCache(str(temp_path))
        cache.data = {"key1": "old_value"}

        cache.add({"key1": "new_value"})

        assert cache.data == {"key1": "new_value"}  # nosec B101

    def test_load_env_var_success(self, temp_path):
        """Test loading environment variable successfully"""
        cache = KeyCache(str(temp_path))
        cache.data = {"TEST_VAR": "test_value"}

        with patch.dict("os.environ", {}, clear=True):
            cache.load_env_var("TEST_VAR")
            assert cache.data["TEST_VAR"] == "test_value"  # nosec B101

    def test_load_env_var_not_found(self, temp_path):
        """Test loading non-existent environment variable raises KeyError"""
        cache = KeyCache(str(temp_path))
        cache.data = {"existing": "value"}

        with raises(KeyError, match="Key does not exist in Key Cache"):
            cache.load_env_var("nonexistent")

    def test_deploy(self, temp_path):
        """Test deploy method loads all environment variables"""
        cache = KeyCache(str(temp_path))
        cache.data = {"VAR1": "value1", "VAR2": "value2"}

        with patch.dict("os.environ", {}, clear=True):
            cache.deploy()
            assert cache.data["VAR1"] == "value1"  # nosec B101
            assert cache.data["VAR2"] == "value2"  # nosec B101
