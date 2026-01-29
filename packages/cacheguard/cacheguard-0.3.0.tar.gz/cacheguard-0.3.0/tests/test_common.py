# Tooling used for creating parameterized tests

from pytest import fixture


@fixture(autouse=True)
def set_age_env_var(monkeypatch):
    """Set a dummy path to allow patched age calls to work"""
    monkeypatch.setenv("CACHEGUARD_AGE_IDENTITY_PATH", "/home/pytest/age.keys")


def generate_params(key_str: str):
    """Generate params and use either encrypt or decrypt"""
    return [
        ("age", f"cacheguard.base_cache.age_{key_str}crypt"),
        ("sops", f"cacheguard.base_cache.sops_{key_str}crypt"),
    ]


def decrypt_params():
    return generate_params("de")


def encrypt_params():
    return generate_params("en")
