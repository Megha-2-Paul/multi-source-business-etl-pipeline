"""Exceptions raised while extracting source data."""


class ExtractionError(Exception):
    """Base exception for expected source extraction failures."""


class SourceFileError(ExtractionError):
    """A local source file is missing, unreadable, or structurally invalid."""


class APIExtractionError(ExtractionError):
    """An API request or response could not be extracted safely."""
