from shutil import which

from pytest import fixture, mark, raises

from cacheguard.age import age_decrypt, age_encrypt, age_execute

AGE_TEST_PUBKEY = "age1c6mghf7wu60rfeek0e87sc4ytykx3vvfyfj38sg8w0ssqdmpe4qqsrs0t9"
AGE_TEST_KEY = (
    "AGE-SECRET-KEY-18UL5WN08DZT8D5FRV7T7AS9TZXEZC6QKGQD8UNQVGW6GLK30MSYQSD0L55"
)

TEST_MESSAGE = "sphinx of black quartz judge my vow\n"
TEST_ARMORED_MESSAGE = """-----BEGIN AGE ENCRYPTED FILE-----
YWdlLWVuY3J5cHRpb24ub3JnL3YxCi0+IFgyNTUxOSBpaWFHZWlUVDRsTmRrTk9s
enRVQUV2eE5qYTNQTzl5cUpJcEhQcG1iQ1NBClpSdEFEa0JHUnU2N1FJMmdhYy9z
UDNhYzJ3bjJhbkJycTNSTkx4VXlzQTAKLS0tIFF3WmhsemZvVnNpamxxcjBCWGwv
WGFtR0NNdHdKUTRGMDl0OWtlNXFOSmsKFT/n/Gl+D1aLZFpmKm/Xgxzdg13Kx3ek
mOr7yDwkTwF2nvK7zfoltac9jq1g6bG3b4yssj/YHmesMwhjnfNsCRW25Gw=
-----END AGE ENCRYPTED FILE-----"""


# Age binary is required to run tests
# TODO: specify age binary via environment
if not which("age"):
    raise RuntimeError("Age binary is required to run age backend test for Cacheguard")


@fixture(scope="class")
def age_key(tmp_path_factory):
    """Create the temporary identity file to be readable during tests"""
    base_dir = tmp_path_factory.mktemp("TestAge")
    key = base_dir / "age_key"
    key.write_text(AGE_TEST_KEY)
    return key


@mark.usefixtures("age_key")
class TestAge:
    def test_age_encryption_regex(self, age_key):
        with raises(ValueError, match="Age pubkey .+"):
            age_encrypt(TEST_MESSAGE, ["an invalid age key"])

    def test_age_execution_binary_error(self):
        with raises(RuntimeError, match="Specified age binary .+"):
            age_execute([], stdin="", age_binary="invalid-age-binary")

    def test_age_execution_stder(self):
        """Pass something invalid to cause the age binary to throw an error"""
        with raises(RuntimeError, match="Age error: .+"):
            # Attempt decryption but flip and pass the message as a key, which will throw an error
            age_execute(["-d", "-i", TEST_ARMORED_MESSAGE], stdin=TEST_ARMORED_MESSAGE)

    def test_age_round_trip(self, age_key):
        """
        It is impossible to have a fixed output for test data as age will not produce the same
        output on each run, so the round trip must be tested to verify encryption portion.
        A simple comparison to the above armored message will not work as expected.
        `test_age_decryption` will identify issues with decryption and this will identify issues
        with both encryption and decryption.
        """
        encrypted_message = age_encrypt(TEST_MESSAGE, [AGE_TEST_PUBKEY])
        decrypted_message = age_decrypt(str(age_key), encrypted_message)
        assert decrypted_message == TEST_MESSAGE  # nosec B101

    def test_age_decryption(self, age_key):
        """
        Partially redundant test, exists to narrow down issues with round-trip to verify the decryption
        part of the function separately.
        """
        decrypted_message = age_decrypt(str(age_key), TEST_ARMORED_MESSAGE)
        assert decrypted_message == TEST_MESSAGE  # nosec B101
