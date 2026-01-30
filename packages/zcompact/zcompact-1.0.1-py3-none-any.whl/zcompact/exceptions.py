"""Exceptions for zcompact."""


class ZcompactError(Exception):
    """Base exception for zcompact errors."""
    pass


class RecordNotFoundError(ZcompactError):
    """Raised when a record is not found."""
    pass


class ArchiveError(ZcompactError):
    """Raised when there's an error with the archive."""
    pass
