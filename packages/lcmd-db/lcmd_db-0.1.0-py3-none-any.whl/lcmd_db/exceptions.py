"""Exceptions for LCMD-DB client."""


class LCMDError(Exception):
    """Base exception for LCMD client."""


class DatasetNotFoundError(LCMDError):
    """Raised when a dataset/subset doesn't exist."""


class DownloadError(LCMDError):
    """Raised when download fails."""
