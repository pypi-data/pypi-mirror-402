"""
EarthScope User ID (EUID) utilities
"""

import base64


def encode_euid_b64(euid: str):
    """
    Base64 encode an EarthScope User ID (EUID) for use in fields with strict character requirements.
    """
    if "|" not in euid and not euid.endswith("@clients"):
        raise ValueError(
            f"Input is not a valid EUID: '{euid}'. Is EUID already encoded?"
        )

    as_bytes = base64.urlsafe_b64encode(euid.encode("utf-8")).rstrip(b"=")

    return as_bytes.decode("utf-8")


def decode_euid_b64(euid_b64: str):
    """
    Base64 decode an EarthScope User ID (EUID) from a field with strict character requirements.
    """
    # extra padding is ignored, but missing padding errors, so we stuff `==` on the end
    with_padding = euid_b64 + "=="

    try:
        return base64.urlsafe_b64decode(with_padding).decode("utf-8")
    except UnicodeDecodeError as e:
        # encoding should always be decodable as UTF-8
        raise ValueError(
            f"EUID could not be decoded from input: '{euid_b64}'. Is EUID already decoded?"
        ) from e
