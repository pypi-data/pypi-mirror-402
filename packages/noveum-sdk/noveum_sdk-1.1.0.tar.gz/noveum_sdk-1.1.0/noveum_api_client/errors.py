"""Contains shared errors types that can be raised from API functions"""

from .constants import UNEXPECTED_STATUS_MESSAGE


class UnexpectedStatus(Exception):
    """Raised by api functions when the response status an undocumented status and Client.raise_on_unexpected_status is True"""

    def __init__(self, status_code: int, content: bytes):
        self.status_code = status_code
        self.content = content

        super().__init__(
            UNEXPECTED_STATUS_MESSAGE.format(
                status_code=status_code,
                content=content.decode(errors="ignore")
            )
        )


__all__ = ["UnexpectedStatus"]
