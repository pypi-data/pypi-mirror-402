from json import loads
from shutil import which
from subprocess import CompletedProcess, run  # nosec B404

# This entire module will not function without Sops in the path
if not (SOPS_BINARY := which("sops")):
    raise RuntimeError("Sops not detected, get it at https://getsops.io/")


def sops_execute(command, input) -> CompletedProcess:
    """Wrapper for Subprocess run with desired conditions"""
    return run(command, input=input, capture_output=True, text=True, timeout=4)  # nosec B603


def sops_encrypt(data: str, age_pubkeys: list = [], pgp_fingerprints: list = []) -> str:
    """Encrypt a string using Sops, via either AGE and/or PGP"""
    sops_command = ["sops", "-e"]

    # flatten the list into a string, then add it to the commands
    args_dict = {
        "-a": age_pubkeys,
        "-p": pgp_fingerprints,
    }

    for key, value in args_dict.items():
        if not value:
            continue
        sops_command += [key, ",".join(value)]

    sops_command += ["/dev/stdin"]

    encrypted_data = sops_execute(sops_command, input=data)
    return encrypted_data.stdout


def sops_decrypt(data) -> str:
    """Simple decryption of an encrypted sops structure"""
    command = [SOPS_BINARY, "decrypt"]
    output = sops_execute(command, input=data)

    # WIP: Exit code and error handling
    return output.stdout


def sops_get_recipients(sops_data: str) -> dict[str, list]:
    """Parse a sops structure for the recipients"""
    sops_dict = loads(sops_data)

    output: dict[str, list] = {}

    def get_keys(key_type: str, lookup: str):
        """Closure to get the keys of a certain types"""
        return [x.get(lookup) for x in sops_dict["sops"].get(key_type)]

    key_dict = {
        "age_pubkeys": ("age", "recipient"),
        "pgp_fingerprints": ("pgp", "fp"),
    }

    for key, value in key_dict.items():
        recipients = get_keys(*value)

        if recipients[0] is None:
            continue

        output[key] = recipients

    return output


def add_to_sops(new_data, sops_data):
    """Add new data to an existing sops structure while maintaining the recipients"""
    recipients = sops_get_recipients(sops_data)
    new_data = sops_decrypt(sops_data) + new_data
    return sops_encrypt(new_data, **recipients)
