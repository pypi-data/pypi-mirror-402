class PhilVaultError(Exception):
    """Base error for the PhilVault SDK."""


class PhilVaultHTTPError(PhilVaultError):
    """HTTP error returned by the PhilVault API."""

    def __init__(self, status_code: int, message: str, payload=None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload
