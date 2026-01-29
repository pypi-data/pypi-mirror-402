# Python Modules
from datetime import datetime
from enum import Enum
from os import environ, path
from pathlib import Path
from shutil import move

# Local Modules
from cacheguard.age import age_decrypt, age_encrypt
from cacheguard.sops import sops_decrypt, sops_encrypt


class Backend(Enum):
    AGE = "age"
    SOPS = "sops"


class BaseCache:
    """Mechanism for sealing and protecting a dataset at rest"""

    def __init__(
        self,
        cache_path: str,
        age_pubkeys: list[str] = [],
        pgp_fingerprints: list[str] = [],
        backend: str = "sops",
        age_identity_path: str = "",
        *args,
        **kwargs,
    ) -> None:
        self.age_pubkeys = age_pubkeys
        self.pgp_fingerprints = pgp_fingerprints
        self.cache_path = cache_path
        self.age_identity_path = age_identity_path

        if backend not in Backend:
            raise ValueError("Cacheguard caches only support 'age' or 'sops' backends.")

        self.backend = Backend(backend)

        if self.backend == Backend.AGE and pgp_fingerprints != []:
            print("Cacheguard Warning: Age backend does not use PGP fingerprints")

        self.data = self.load() if path.exists(cache_path) else ""

    def decrypt(self, message: str, identity_path: str | None = "") -> str:
        """Simple wrapper for matching the decryption backend"""
        if self.backend == Backend.AGE:
            # Get a valid identity from one of the possible sources
            for item in [
                identity_path,
                self.age_identity_path,
                environ.get("CACHEGUARD_AGE_IDENTITY_PATH"),
            ]:
                if item:
                    identity_path = item
                    print(item)
                    break

            if not identity_path:
                raise ValueError(
                    "Cacheguard age backend requires explicit age identity path passed for decryption or CACHEGUARD_AGE_IDENTITY_PATH environment variable set."
                )
            return age_decrypt(identity_path, message)
        else:
            # TODO: check for Sops environment variables and/or add explicit identity
            return sops_decrypt(message)

    def encrypt(self, data: str) -> str:
        """Simple wrapper for matching the encryption backend"""
        if self.backend == Backend.AGE:
            return age_encrypt(data, self.age_pubkeys)
        else:
            return sops_encrypt(data, self.age_pubkeys, self.pgp_fingerprints)

    def load(self) -> str:
        """Unseal the dataset"""
        try:
            with open(self.cache_path) as f:
                contents = f.read()
            data = self.decrypt(contents)
        except OSError:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_file_name = f"archive-{timestamp}-{Path(self.cache_path).name}"
            new_path = Path(self.cache_path).parent / new_file_name
            move(self.cache_path, new_path)
            print(
                f"[CacheGuard] Warning: Cache JSON error - old cache potentially corrupt or empty.\n - Created new one and archived original at: {new_path}"
            )
            return ""  # The file was not valid and was empty or corrupt
        else:
            return data

    def save(self, data_string) -> None:
        """Write the dataset to the encrypted at-rest state"""
        encrypted_data = self.encrypt(data_string)

        if not path.exists(self.cache_path):
            # make it
            Path(self.cache_path).parent.mkdir(parents=True, exist_ok=True)
            Path(self.cache_path).touch(exist_ok=True)
        with open(self.cache_path, "w") as f:
            f.write(encrypted_data)

    def add(self, *args, **kwargs):
        """"""
        raise NotImplementedError("Incorrect cache type - method for Key Cache")

    def append(self, *args, **kwargs):
        """"""
        raise NotImplementedError("Incorrect cache type - method for Text Cache")
