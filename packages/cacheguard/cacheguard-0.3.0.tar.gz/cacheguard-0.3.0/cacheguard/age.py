from re import match
from shutil import which
from subprocess import run  # nosec B404


def age_execute(args: list[str], stdin: str, age_binary: str = "age") -> str:
    """
    Helper for executing and handling Age command line calls

    Args:
        args: list of string that are the command-line args that would be otherwise space separated if typed out
        stdin: the actual stdin used, which is typically the message to be encrypted or decrypted

    Returns:
        string value of the operation's stdout
    """
    if not which(age_binary):
        raise RuntimeError(
            f"Specified age binary ({age_binary}) not found, please install via your preferred package manager."
        )

    command = [age_binary] + args

    result = run(command, input=stdin, capture_output=True, text=True, timeout=5)  # nosec B603

    if result.stderr:
        raise RuntimeError(f"Age error: {result.stderr}")

    return result.stdout


def age_encrypt(content: str, recipients: list[str]) -> str:
    """
    Encrypt a string using age.

    Args:
        content: string value to be encrypted as the message body
        recipients: list of strings containing age pubkeys, may include ED25519 SSH pubkeys as well

    Returns:
        string that is armored (ascii/console-safe) age encrypted message
    """
    # `-a` represents armor/ascii output, making the text console-safe
    args_list = ["-e", "-a"]
    for recipient in recipients:
        # Simple match that matches most valid age and ed25519 pubkeys
        if not match(
            r"(^age1[!-~]+$)|(^ssh-ed25519\s+[A-Za-z0-9+]+={0,2}(?:\s+.*)?$)", recipient
        ):
            raise ValueError(f"Age pubkey ({recipient}) is not valid.")
        args_list.extend(["-r", recipient])

    return age_execute(args=args_list, stdin=content)


def age_decrypt(identity_path: str, age_content: str) -> str:
    """
    Decrypt an age-encrypted string.

    Args:
        identity_path: string value to file location with an identity recipient to decrypt the file
        age_content: string value of the actual text of the age-encrypted message

    returns:
        string of decrypted age message

    Notes:
        Cacheguard only natively uses "armored" age messages that are ascii and not binary
        Binary in the console may have unwanted effects, it is not recommended to pass binary directly
    """
    # TODO: validate identity path
    return age_execute(["-d", "-i", identity_path], age_content)
