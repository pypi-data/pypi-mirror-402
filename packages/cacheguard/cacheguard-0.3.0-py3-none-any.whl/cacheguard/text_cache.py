# Python Modules
from io import StringIO

# Project Modules
from cacheguard.base_cache import BaseCache


class TextCache(BaseCache):
    """Plain-text edition of the cache"""

    def __init__(
        self,
        sops_path: str,
        age_pubkeys: list[str] = [],
        pgp_fingerprints: list[str] = [],
        backend: str = "sops",
        newline: str = "\n",
        age_identity_path: str = "",
    ):
        super().__init__(
            sops_path, age_pubkeys, pgp_fingerprints, backend, age_identity_path
        )
        self.buffer = StringIO()
        self.newline = newline

        # Add the existing data
        if self.data:
            for line in self.data.split(newline):
                self.append(line)

    def load(self) -> str:
        """Handle the plain text version of the cache"""
        data = super().load()
        self.buffer = StringIO(data)
        return data

    def save(self, data_string=None) -> None:
        """Write the dataset to the encrypted at-rest state"""
        if data_string is None:
            data_string = self.buffer.getvalue().strip()
        super().save(data_string)

    def append(self, string: str) -> None:
        """Simple method to add more string content"""
        self.buffer.write(string + self.newline)
