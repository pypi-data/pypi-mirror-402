# Python Modules
from json import dumps, loads
from os import environ

# Project Modules
from cacheguard.base_cache import BaseCache


class KeyCache(BaseCache):
    """Key-Value edition of the Cache"""

    def __init__(
        self,
        sops_path: str,
        age_pubkeys: list[str] = [],
        pgp_fingerprints: list[str] = [],
        backend: str = "sops",
        age_identity_path: str = "",
    ) -> None:
        super().__init__(
            sops_path, age_pubkeys, pgp_fingerprints, backend, age_identity_path
        )
        if not self.data:
            self.data = {}

    def load(self) -> dict:  # type: ignore[override]
        """Handle the data for key-values by loading with JSON"""
        if obtained_data := super().load():
            self.data = loads(obtained_data)
        else:
            self.data = {}
        return self.data

    def save(self, *args, **kwargs) -> None:
        """Write the dataset to the encrypted at-rest state"""
        converted_string = dumps(self.data)
        super().save(converted_string)

    def add(self, entry: dict) -> None:
        """Add new entries"""
        self.data = {**self.data, **entry}

    def load_env_var(self, env_var) -> None:
        """Load a key-value pair into the environment from the cache"""
        if not self.data.get(env_var):
            raise KeyError("Key does not exist in Key Cache")
        environ[env_var] = self.data[env_var]

    def deploy(self) -> None:
        """Load every key-value pair in this cache into the environment"""
        for key in self.data.keys():
            self.load_env_var(key)
