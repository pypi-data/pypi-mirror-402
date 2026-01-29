"""
Test for the `cacheguard.sops` module, which contains helper functions for
interfacing with Sops via Subprocess
"""

from cacheguard.sops import sops_encrypt, sops_get_recipients

# These are dummy values
TEST_AGE_PUBKEY = (
    "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINylqNJ7MbeAA/YYa0rXQhFukbnXh0ZFKNQISigutI2v"
)
TEST_GPG_FINGERPRINT = "31F5A7299414BD57611F2A2A28737947AD89864B"
TEST_DATA = "This is only a test"

SAMPLE_SOPS = '{\n\t"data": "ENC[AES256_GCM,data:1zEA/X07evo3IDtIa5JJLuNEuQ==,iv:pLahAlF+0a8Sp47iWiZp9YcasUMwmKB2GNkbDJfgGSM=,tag:e7GktF7mcinTw9xTSeLwBA==,type:str]",\n\t"sops": {\n\t\t"age": [\n\t\t\t{\n\t\t\t\t"recipient": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINylqNJ7MbeAA/YYa0rXQhFukbnXh0ZFKNQISigutI2v",\n\t\t\t\t"enc": "-----BEGIN AGE ENCRYPTED FILE-----\\nYWdlLWVuY3J5cHRpb24ub3JnL3YxCi0+IHNzaC1lZDI1NTE5IDdZZGkwdyBzdWdE\\nSnZYQ3VpMU1zbzZvLzgvZ1FVUUtxOVp6S2NGNDYwSlUzNHQrU3pZClNUOEdZaFl1\\nNzN3aUpaR1JlSTZ6R1krdkxkSW1YeHd6N3pDczNyT2c5bjAKLS0tIGhlV3NkeVdv\\nM3U1anZBUjFKYUkwUlJQdVF2bHo0ZW4zS2hoK3kwVlVZeEkKYRlxqK7nvd8jPPr+\\nN6cRMhRazQMMGLmOB/UeFRxuMPuqxobsk1/A8yN7rTkJEZJPjXRgZ5OIhDZjYAsD\\nNwV8ag==\\n-----END AGE ENCRYPTED FILE-----\\n"\n\t\t\t}\n\t\t],\n\t\t"lastmodified": "2025-09-24T19:39:58Z",\n\t\t"mac": "ENC[AES256_GCM,data:ydFrS3TwwxN+VJ4+YXj3FCXsby9wf0wuBSC7R9CvS/xxXqCvywzoPMGWuGMKFRW6XNgLXslPNmlC5zVeLktFkSK4WsLsLff1uQ6yF49vU23l7HXinckrhZQT9AdxwDanp6CArcBJySm5qBLMoyX1ixJteE4rvAOWUIdiIb54D6g=,iv:LrmIL4PCqBi0L0gTFJmkm2gorgIvxbVUi3rX5AVgoko=,tag:gD7q03sDBg/1bHE9MSWLzA==,type:str]",\n\t\t"pgp": [\n\t\t\t{\n\t\t\t\t"created_at": "2025-09-24T19:39:58Z",\n\t\t\t\t"enc": "-----BEGIN PGP MESSAGE-----\\n\\nhQEMA1mP5Oz/gIJzAQf9F9DPO2NjWAdqvDBWusqHuaCSoQ+tsvibTYKnQYxEw/WL\\nQMmw6vkaXUEZb8bL0JQoZ26BWeE5TF/ovIi0FqX+IPRR/MKHQJKriHlTOSd6NvE/\\nNDxeBj6Drw/m9MeTaS8wExytUUB15OamthxwbrlLN+kqeoxZ4s95GJWKxGhGxXaL\\ng66/OhvenMs3ZFw/MmIxJsdayiJzxy6UcdxGJsXKwwkMFg1n2lg9EMRtDflYE2+Z\\nk4Vw3xnDt6qcebvCZ6Jn2lmUx577FJDfrW3gBI9UPQ5Y74EjZ1J3U2OhZhKAMVAt\\nQv6SeGTWII/CTc0klMNQORsXFbvr50t9I1d198uB19JcAaIGhLOsaApw2jWIUnpE\\nK5JPLGRx/o/oZT44tB3zUsqsZu9OWP7fm5Ny8SMnsnjF3Ws3jxvEEOo2axDw+en8\\no2brmHMZTt0aOsduOtaZMiuadm7LK9/+hjG6qHc=\\n=N9jm\\n-----END PGP MESSAGE-----",\n\t\t\t\t"fp": "31F5A7299414BD57611F2A2A28737947AD89864B"\n\t\t\t}\n\t\t],\n\t\t"unencrypted_suffix": "_unencrypted",\n\t\t"version": "3.10.2"\n\t}\n}\n'


def test_encryption(mocker, monkeypatch):
    mock_run = mocker.patch("cacheguard.sops.run")

    def shutil_patch(*args, **kwargs):
        return "sops"

    monkeypatch.setattr("cacheguard.sops.which", shutil_patch)

    test_kwargs = {
        "data": TEST_DATA,
        "age_pubkeys": [TEST_AGE_PUBKEY],
        "pgp_fingerprints": [TEST_GPG_FINGERPRINT],
    }

    expected_call_args = [
        "sops",
        "-e",
        "-a",
        TEST_AGE_PUBKEY,
        "-p",
        TEST_GPG_FINGERPRINT,
        "/dev/stdin",
    ]

    expected_call = {
        "input": TEST_DATA,
        "capture_output": True,
        "text": True,
        "timeout": 4,
    }

    sops_encrypt(**test_kwargs)

    mock_run.assert_called_with(expected_call_args, **expected_call)


def test_get_recipients():
    result = sops_get_recipients(SAMPLE_SOPS)

    expected_result = {
        "age_pubkeys": [TEST_AGE_PUBKEY],
        "pgp_fingerprints": [TEST_GPG_FINGERPRINT],
    }

    assert result == expected_result  # nosec B101
